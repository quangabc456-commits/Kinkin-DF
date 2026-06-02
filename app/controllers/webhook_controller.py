from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Optional

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.core.config import settings
from app.core.db import get_session
from app.models import CauHinh, DuLieuSheet, HanhTrinhPgh, PhieuGiaoHang


router = APIRouter(prefix="/webhook", tags=["webhook"])


TRANG_THAI_CUOI = {101, 107, 201, 501, 503, 504}


def _sync_sheet_bg(sheet_name: str) -> None:
    from app.services.sheet_sync import sync_sheet

    try:
        sync_sheet(sheet_name)
    except Exception as e:
        print(f"[webhook sync] {sheet_name}: lỗi {e}")


def _parse_vtp_datetime(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    for fmt in ("%d/%m/%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%d-%m-%Y %H:%M:%S"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


@router.post("/vtp")
async def nhan_webhook_vtp(
    request: Request,
    authorization: Optional[str] = Header(default=None),
) -> dict[str, Any]:
    payload = await request.json()

    with get_session() as session:
        if authorization:
            from app.models import TaiKhoanVtp

            tk = session.execute(
                select(TaiKhoanVtp).where(TaiKhoanVtp.webhook_secret == authorization)
            ).scalar_one_or_none()
            if tk is None:
                raise HTTPException(
                    status_code=401, detail="Authorization header không khớp tài khoản nào"
                )

        data = payload.get("DATA") or {}
        ma_van_don = data.get("ORDER_NUMBER")
        ma_trang_thai = data.get("ORDER_STATUS")
        thoi_gian = _parse_vtp_datetime(data.get("ORDER_STATUSDATE"))

        if not ma_van_don or ma_trang_thai is None or thoi_gian is None:
            return {
                "status": "bypass",
                "reason": "thiếu ORDER_NUMBER/ORDER_STATUS/ORDER_STATUSDATE",
            }

        pgh = session.execute(
            select(PhieuGiaoHang).where(PhieuGiaoHang.ma_pgh_vtp == ma_van_don)
        ).scalar_one_or_none()

        stmt = pg_insert(HanhTrinhPgh).values(
            phieu_giao_hang_id=pgh.id if pgh else None,
            ma_van_don_vtp=ma_van_don,
            ma_trang_thai=int(ma_trang_thai),
            ten_trang_thai=data.get("STATUS_NAME"),
            thoi_gian_trang_thai=thoi_gian,
            vi_tri_hien_tai=data.get("LOCATION_CURRENTLY") or data.get("LOCALION_CURRENTLY"),
            ghi_chu=data.get("NOTE"),
            nhan_vien_ten=data.get("EMPLOYEE_NAME"),
            nhan_vien_sdt=data.get("EMPLOYEE_PHONE"),
            dang_chuyen_hoan=data.get("IS_RETURNING"),
            ly_do_ma=data.get("REASON_CODE"),
            pod_images_json=(data.get("POD") or {}).get("IMAGES"),
            payload_raw=payload,
        )
        stmt = stmt.on_conflict_do_nothing(constraint="uq_hanh_trinh_pgh_unique_event")
        session.execute(stmt)

        if pgh is not None and int(ma_trang_thai) in TRANG_THAI_CUOI:
            mapping = {
                501: "hoan_thanh",
                504: "hoan_hang",
                503: "da_huy",
                107: "da_huy",
                201: "da_huy",
                101: "loi_api",
            }
            pgh.trang_thai_pgh = mapping.get(int(ma_trang_thai), pgh.trang_thai_pgh)

    return {"status": "ok"}


@router.post("/sheet-changed")
async def nhan_sheet_changed(
    request: Request,
    background_tasks: BackgroundTasks,
    x_sheet_secret: Optional[str] = Header(default=None, alias="X-Sheet-Secret"),
) -> dict[str, Any]:
    from app.services.sheet_sync import parse_ngay_tu_ten_sheet

    payload = await request.json()

    with get_session() as session:
        secret_row = session.execute(
            select(CauHinh).where(CauHinh.khoa == "WEBHOOK_SECRET")
        ).scalar_one_or_none()
        secret_expected = secret_row.gia_tri if secret_row else None
        sheet_id_row = session.execute(
            select(CauHinh).where(CauHinh.khoa == "SHEET_ID")
        ).scalar_one_or_none()
        sheet_id_expected = sheet_id_row.gia_tri if sheet_id_row else None

    if secret_expected and secret_expected != (x_sheet_secret or ""):
        raise HTTPException(status_code=401, detail="Sai X-Sheet-Secret")

    sent_id = payload.get("spreadsheetId") or ""
    if sheet_id_expected and sent_id != sheet_id_expected:
        return {"status": "bypass", "reason": "spreadsheetId không khớp", "got": sent_id}

    sheet_name = payload.get("sheetName") or ""
    if not sheet_name:
        return {"status": "bypass", "reason": "thiếu sheetName"}

    if parse_ngay_tu_ten_sheet(sheet_name) is None:
        return {"status": "bypass", "reason": f"sheet '{sheet_name}' không phải dạng dd-mm-yy"}

    if not settings.ENABLE_SYNC_UI:
        return {"status": "bypass", "reason": "sync bị tắt (ENABLE_SYNC_UI=false)"}

    background_tasks.add_task(_sync_sheet_bg, sheet_name)
    return {"status": "queued", "sheet": sheet_name}


_ALLOWED_FIELDS = {
    "ten_sheet",
    "ngay_chot",
    "sheet_row_index",
    "ma_kien_k",
    "can_nang_kien_kg",
    "ma_f_cha",
    "ma_thung",
    "ma_van_don",
    "can_nang_kg",
    "phu_thu",
    "ghi_chu",
    "ten_kh",
    "phuong_thuc_gui",
    "thong_tin_gui_raw",
    "nhom_san_pham",
    "dia_chi_nguoi_nhan",
    "sdt_nguoi_nhan",
    "trang_thai_goc",
    "ma_genkin",
    "khoi_luong_genkin_kg",
    "co_match_genkin",
}

_DECIMAL_FIELDS = {"can_nang_kien_kg", "can_nang_kg", "khoi_luong_genkin_kg"}


def _to_decimal(v: Any) -> Optional[Decimal]:
    if v is None or v == "":
        return None
    if isinstance(v, Decimal):
        return v
    try:
        return Decimal(str(v).replace(",", "."))
    except (InvalidOperation, ValueError):
        return None


def _to_date(v: Any) -> Optional[date]:
    if not v:
        return None
    if isinstance(v, date) and not isinstance(v, datetime):
        return v
    s = str(v).strip()
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%d-%m-%y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def _normalize(raw: dict) -> dict:
    out: dict = {}
    for k, v in raw.items():
        if k not in _ALLOWED_FIELDS:
            continue
        if v is None or v == "":
            out[k] = None
            continue
        if k == "ngay_chot":
            out[k] = _to_date(v)
        elif k in _DECIMAL_FIELDS:
            out[k] = _to_decimal(v)
        elif k == "sheet_row_index":
            try:
                out[k] = int(v)
            except (TypeError, ValueError):
                out[k] = None
        elif k == "co_match_genkin":
            if isinstance(v, bool):
                out[k] = v
            else:
                out[k] = str(v).strip().upper() == "TRUE"
        else:
            out[k] = str(v)
    return out


@router.post("/kinkin")
async def nhan_webhook_kinkin(
    request: Request,
    x_kinkin_secret: Optional[str] = Header(default=None, alias="X-Kinkin-Secret"),
) -> dict[str, Any]:
    """Nhận push từ Kinkin: 1 row (object) hoặc list rows giống schema du_lieu_sheet.

    Auth: header X-Kinkin-Secret phải khớp settings.KK_WEBHOOK_SECRET.
    Idempotent: upsert theo (ten_sheet, sheet_row_index).
    """
    if not settings.KK_WEBHOOK_SECRET:
        raise HTTPException(status_code=503, detail="KK_WEBHOOK_SECRET chưa cấu hình")
    if (x_kinkin_secret or "") != settings.KK_WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Sai X-Kinkin-Secret")

    payload = await request.json()
    if isinstance(payload, dict) and "rows" in payload:
        rows_raw = payload.get("rows") or []
    elif isinstance(payload, dict):
        rows_raw = [payload]
    elif isinstance(payload, list):
        rows_raw = payload
    else:
        raise HTTPException(status_code=400, detail="Payload phải là object hoặc list")

    so_them = 0
    so_cap_nhat = 0
    so_bypass = 0
    bypass_reasons: list[dict] = []

    now = datetime.now(timezone.utc)

    with get_session() as session:
        for idx, raw in enumerate(rows_raw):
            if not isinstance(raw, dict):
                so_bypass += 1
                bypass_reasons.append({"i": idx, "reason": "row không phải dict"})
                continue
            row = _normalize(raw)
            row["dong_bo_lan_cuoi_luc"] = now

            if not row.get("ten_sheet") or row.get("sheet_row_index") is None:
                so_bypass += 1
                bypass_reasons.append(
                    {"i": idx, "reason": "thiếu ten_sheet/sheet_row_index"}
                )
                continue
            if not row.get("ma_van_don"):
                so_bypass += 1
                bypass_reasons.append({"i": idx, "reason": "thiếu ma_van_don"})
                continue
            if row.get("ngay_chot") is None:
                so_bypass += 1
                bypass_reasons.append({"i": idx, "reason": "ngay_chot không parse được"})
                continue

            existing = session.execute(
                select(DuLieuSheet.id).where(
                    DuLieuSheet.ten_sheet == row["ten_sheet"],
                    DuLieuSheet.sheet_row_index == row["sheet_row_index"],
                )
            ).first()

            stmt = pg_insert(DuLieuSheet).values(**row).on_conflict_do_update(
                index_elements=["ten_sheet", "sheet_row_index"],
                set_={
                    k: v
                    for k, v in row.items()
                    if k not in ("ten_sheet", "sheet_row_index")
                },
            )
            session.execute(stmt)
            if existing:
                so_cap_nhat += 1
            else:
                so_them += 1

    return {
        "status": "ok",
        "nhan": len(rows_raw),
        "them_moi": so_them,
        "cap_nhat": so_cap_nhat,
        "bypass": so_bypass,
        "bypass_reasons": bypass_reasons[:10],
    }
