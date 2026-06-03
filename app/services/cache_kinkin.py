"""Cache thông tin Kinkin cho từng mã vào DB.

Worker cron gọi `prefetch_codes()` định kỳ.
UI lookup chỉ đọc `cache_kinkin_ma` qua `doc_cache()`, không call API live.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import or_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.core.config import settings
from app.integrations import kinkin_client as kk
from app.integrations.kinkin_client import KinkinError
from app.models import CacheKinkinMa, DuLieuSheet
from app.services.kinkin_lookup import _thu_qua_kho, loai_ma


def _first_item(resp: Any) -> Optional[dict]:
    if not isinstance(resp, dict):
        return None
    data = resp.get("data") if "data" in resp else resp
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                return item
        return None
    if isinstance(data, dict):
        for key in (
            "items",
            "results",
            "list",
            "packageFs",
            "packageVks",
            "packageKs",
            "deliveryOrders",
        ):
            arr = data.get(key)
            if isinstance(arr, list) and arr:
                first = arr[0]
                if isinstance(first, dict):
                    return first
        if any(
            k in data
            for k in (
                "packageFCode",
                "billCode",
                "code",
                "statusName",
                "packageFStatusName",
            )
        ):
            return data
    return None


def _parse_dt(v: Any) -> Optional[datetime]:
    if not v:
        return None
    if isinstance(v, datetime):
        return v
    s = str(v).strip()
    for fmt in (
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%d/%m/%Y %H:%M:%S",
        "%d-%m-%Y %H:%M:%S",
        "%Y-%m-%d",
    ):
        try:
            return datetime.strptime(s.split("Z")[0].split("+")[0], fmt)
        except ValueError:
            continue
    return None


def _pick(item: dict, *keys: str) -> Any:
    for k in keys:
        v = item.get(k)
        if v not in (None, ""):
            return v
    return None


def _to_int(v: Any) -> Optional[int]:
    if v is None or v == "":
        return None
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None


def _trich_fields(loai: str, item: dict, kho_match: Optional[str]) -> dict[str, Any]:
    """Best-effort extract từ 1 record Kinkin → các cột tiếng Việt của cache_kinkin_ma."""
    return {
        "loai": loai,
        "ma_don_chinh": _pick(item, "packageFCode", "packageFName", "code", "packageCode"),
        "bill_code": _pick(item, "billCode", "deliveryCode", "orderCode", "mawb"),
        "trang_thai": _pick(
            item,
            "packageFStatusName",
            "currentPackageFStatusName",
            "statusName",
            "status",
            "statusText",
            "billStatus",
        ),
        "ten_kho": _pick(
            item,
            "wareHouseName",
            "warehouseName",
            "kho",
            "departureWarehouseName",
            "rotationWareHouseName",
        ),
        "warehouse_id": str(_pick(item, "wareHouseId", "warehouseId") or kho_match or "") or None,
        "ma_kien_k": _pick(item, "packageKCode", "packageKName", "kCode"),
        "ma_f_cha": _pick(item, "packageFFatherCode", "fatherCode"),
        "ma_thung": _pick(item, "packageFSonCode", "sonCode", "packageBoxCode"),
        "nguoi_nhan": _pick(item, "customerName", "receiverName", "userName", "fullName"),
        "sdt_nguoi_nhan": _pick(item, "customerPhone", "receiverPhone", "phone", "phoneNumber"),
        "dia_chi_nhan": _pick(
            item, "customerAddress", "receiverAddress", "address", "destinationAddress"
        ),
        "nha_van_chuyen": _pick(
            item, "shippingPartner", "carrierName", "shippingMethod", "partnerName"
        ),
        "so_luong": _to_int(_pick(item, "quantity", "totalQuantity")),
        "tong_tien_vnd": _to_int(_pick(item, "totalAmount", "totalPrice", "grandTotal")),
        "ngay_tao_kinkin": _parse_dt(
            _pick(item, "billDate", "createdDate", "createdAt", "creationDate", "importDate")
        ),
        "ngay_cap_nhat_kinkin": _parse_dt(
            _pick(item, "billClosedDate", "modifiedDate", "updatedDate", "lastModifiedDate")
        ),
    }


def _goi_api_theo_loai(code: str, loai: str) -> tuple[Optional[Any], Optional[str]]:
    """Call API phù hợp với loại mã. Trả (raw_response, warehouse_match)."""
    if loai == "F":
        resp, kho, _ = _thu_qua_kho(kk.f_list, code)
        return resp, kho
    if loai == "K":
        resp, kho, _ = _thu_qua_kho(kk.k_list, code)
        return resp, kho
    if loai == "VK":
        return kk.vk_list(code), None
    if loai in ("PGH", "HD"):
        return kk.pgh_detail_by_code(code), None
    if loai == "GKA":
        resp, kho, _ = _thu_qua_kho(kk.pgh_list, search_content=code, page=1, page_size=5)
        return resp, kho
    resp, kho, _ = _thu_qua_kho(kk.pgh_list, search_content=code, page=1, page_size=5)
    return resp, kho


def prefetch_code(session: Session, code: str) -> dict[str, Any]:
    """Call API Kinkin cho 1 mã → upsert vào cache_kinkin_ma. Return summary dict."""
    code = (code or "").strip()
    if not code:
        return {"code": code, "status": "skip", "reason": "empty"}

    loai = loai_ma(code)
    now = datetime.now(timezone.utc)

    try:
        raw, kho_match = _goi_api_theo_loai(code, loai)
    except KinkinError as e:
        stmt = pg_insert(CacheKinkinMa).values(
            code=code, loai=loai, last_sync_luc=now, last_sync_loi=str(e)[:500]
        ).on_conflict_do_update(
            index_elements=["code"],
            set_={"last_sync_luc": now, "last_sync_loi": str(e)[:500]},
        )
        session.execute(stmt)
        return {"code": code, "status": "loi_api", "loi": str(e)}

    item = _first_item(raw)
    extracted = _trich_fields(loai, item, kho_match) if item else {"loai": loai}
    extracted["payload_raw"] = raw if isinstance(raw, (dict, list)) else None
    extracted["last_sync_luc"] = now
    extracted["last_sync_loi"] = None if item else "Không có data từ API"

    stmt = pg_insert(CacheKinkinMa).values(code=code, **extracted).on_conflict_do_update(
        index_elements=["code"],
        set_={k: v for k, v in extracted.items()},
    )
    session.execute(stmt)
    return {"code": code, "status": "ok" if item else "trong", "ma_don": extracted.get("ma_don_chinh")}


def chon_codes_can_refresh(
    session: Session, batch: int, days_back: int, stale_hours: int = 6
) -> list[str]:
    """Lấy danh sách mã unique cần refresh:
       - Có trong du_lieu_sheet với ngay_chot >= max(today - days_back, CRON_WORKER_MIN_NGAY_CHOT)
       - Chưa có trong cache_kinkin_ma HOẶC last_sync_luc > stale_hours.
    """
    cutoff_date = date.today() - timedelta(days=days_back)
    if settings.CRON_WORKER_MIN_NGAY_CHOT:
        try:
            min_ngay = date.fromisoformat(settings.CRON_WORKER_MIN_NGAY_CHOT)
            cutoff_date = max(cutoff_date, min_ngay)
        except ValueError:
            pass
    cutoff_sync = datetime.now(timezone.utc) - timedelta(hours=stale_hours)

    sub_recent = (
        select(DuLieuSheet.ma_van_don)
        .where(
            DuLieuSheet.ngay_chot >= cutoff_date,
            DuLieuSheet.ma_van_don.is_not(None),
        )
        .distinct()
        .subquery()
    )

    rows = session.execute(
        select(sub_recent.c.ma_van_don)
        .outerjoin(CacheKinkinMa, CacheKinkinMa.code == sub_recent.c.ma_van_don)
        .where(
            or_(
                CacheKinkinMa.id.is_(None),
                CacheKinkinMa.last_sync_luc.is_(None),
                CacheKinkinMa.last_sync_luc < cutoff_sync,
            )
        )
        .limit(batch)
    ).all()
    return [r[0] for r in rows if r[0]]


def prefetch_batch(
    session: Session, batch: int, days_back: int, stale_hours: int = 6
) -> dict[str, Any]:
    if not settings.KK_USERNAME or not settings.KK_PASSWORD:
        return {"status": "skip", "reason": "Thiếu KK_USERNAME/KK_PASSWORD"}

    codes = chon_codes_can_refresh(session, batch, days_back, stale_hours)
    so_ok = 0
    so_loi = 0
    so_trong = 0

    for code in codes:
        try:
            kq = prefetch_code(session, code)
            if kq["status"] == "ok":
                so_ok += 1
            elif kq["status"] == "trong":
                so_trong += 1
            else:
                so_loi += 1
        except Exception:
            so_loi += 1

    return {
        "status": "ok",
        "quet": len(codes),
        "thanh_cong": so_ok,
        "trong": so_trong,
        "loi": so_loi,
    }


def doc_cache(session: Session, code: str) -> Optional[CacheKinkinMa]:
    return session.execute(
        select(CacheKinkinMa).where(CacheKinkinMa.code == code).limit(1)
    ).scalar_one_or_none()
