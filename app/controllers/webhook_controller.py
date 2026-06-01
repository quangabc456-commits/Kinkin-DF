from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.core.config import settings
from app.core.db import get_session
from app.models import CauHinh, HanhTrinhPgh, PhieuGiaoHang


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
