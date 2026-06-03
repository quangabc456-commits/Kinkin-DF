from __future__ import annotations

from datetime import date, timedelta, datetime, timezone
from typing import Any, Optional

from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.integrations import kinkin_client as kk
from app.integrations.kinkin_client import KinkinError
from app.models import DuLieuSheet
from app.services.kinkin_lookup import _thu_qua_kho


def _trich_trang_thai(resp: Any) -> Optional[str]:
    """Best-effort: rút text trạng thái từ response Kinkin pgh_list/f_list."""
    if not isinstance(resp, dict):
        return None
    data = resp.get("data") if "data" in resp else resp
    if isinstance(data, dict):
        for key in ("items", "results", "list", "packageFs", "deliveryOrders"):
            arr = data.get(key)
            if isinstance(arr, list) and arr:
                first = arr[0]
                if isinstance(first, dict):
                    for k in ("statusName", "status", "billStatus", "statusText"):
                        v = first.get(k)
                        if v:
                            return str(v)
    return None


def _min_ngay_chot() -> Optional[date]:
    if not settings.CRON_WORKER_MIN_NGAY_CHOT:
        return None
    try:
        return date.fromisoformat(settings.CRON_WORKER_MIN_NGAY_CHOT)
    except ValueError:
        return None


def _rows_can_refresh(
    session: Session, batch: int, days_back: int
) -> list[DuLieuSheet]:
    cutoff = date.today() - timedelta(days=days_back)
    min_ngay = _min_ngay_chot()
    cutoff_eff = max(cutoff, min_ngay) if min_ngay else cutoff
    rows = session.execute(
        select(DuLieuSheet)
        .where(
            DuLieuSheet.ngay_chot >= cutoff_eff,
            DuLieuSheet.ma_van_don.is_not(None),
            or_(
                DuLieuSheet.trang_thai_goc.is_(None),
                DuLieuSheet.trang_thai_goc == "",
            ),
        )
        .order_by(DuLieuSheet.ngay_chot.desc(), DuLieuSheet.id.desc())
        .limit(batch)
    ).scalars().all()
    return list(rows)


def refresh_status_batch(
    session: Session,
    batch: int = 50,
    days_back: int = 7,
) -> dict[str, Any]:
    """Quét N dòng gần đây thiếu trang_thai_goc → call Kinkin pgh_list để lấy status text.

    Không raise; lỗi từng dòng ghi vào counters.
    """
    if not settings.KK_USERNAME or not settings.KK_PASSWORD:
        return {"status": "skip", "reason": "Thiếu KK_USERNAME/KK_PASSWORD"}

    rows = _rows_can_refresh(session, batch, days_back)
    so_cap_nhat = 0
    so_loi = 0
    so_khong_co_data = 0
    lo_loi: list[dict] = []

    for r in rows:
        try:
            resp, _kho, _da_thu = _thu_qua_kho(
                kk.pgh_list, search_content=r.ma_van_don, page=1, page_size=5
            )
            trang_thai = _trich_trang_thai(resp)
            if trang_thai:
                r.trang_thai_goc = trang_thai
                r.dong_bo_lan_cuoi_luc = datetime.now(timezone.utc)
                so_cap_nhat += 1
            else:
                so_khong_co_data += 1
        except KinkinError as e:
            so_loi += 1
            if len(lo_loi) < 5:
                lo_loi.append({"ma_van_don": r.ma_van_don, "loi": str(e)})

    return {
        "status": "ok",
        "quet": len(rows),
        "cap_nhat": so_cap_nhat,
        "khong_co_data": so_khong_co_data,
        "loi": so_loi,
        "lo_loi": lo_loi,
    }
