"""Hợp nhất: tạo PGH kho đến (+ VTP qua partner* nếu chọn) rồi GHI vào phieu_giao_hang.

Tách phần persist DB ra khỏi `tao_pgh_kho_den` (chỉ lo gọi API). Controller gọi
`tao_pgh_dia_chi_cu/moi(..., vtp=...)` để tạo, rồi `luu_ket_qua(...)` để lưu.
"""
from __future__ import annotations

import secrets
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import DuLieuSheet, PhieuGiaoHang


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _sinh_ma_noi_bo() -> str:
    return "KK" + _now().strftime("%y%m%d") + secrets.token_hex(4).upper()


def _extract(resp: Any, keys: tuple[str, ...]) -> Optional[str]:
    """Bóc mã từ response (best-effort — shape add-update-delivery cần xác minh hệ thật)."""
    if not isinstance(resp, dict):
        return None
    data = resp.get("data")
    # Không nhận data dạng bool/"true"/"false" làm mã (deliveryAddress/save trả data:true)
    if isinstance(data, str) and data and data.lower() not in ("true", "false"):
        return data
    if isinstance(data, dict):
        for k in keys:
            if data.get(k):
                return str(data[k])
    for k in keys:
        if resp.get(k):
            return str(resp[k])
    return None


def luu_ket_qua(
    session: Session,
    ds: DuLieuSheet,
    kq: Optional[dict],
    *,
    ok: bool,
    loi: Optional[str] = None,
    receiver: str = "",
    receive_phone: str = "",
    address: str = "",
    co_vtp: bool = False,
) -> PhieuGiaoHang:
    """Find-or-create phieu_giao_hang theo du_lieu_sheet_id, cập nhật kết quả kho đến (+VTP)."""
    resp = kq.get("resp") if kq else None
    body = kq.get("request") if kq else None

    pgh = (
        session.execute(
            select(PhieuGiaoHang)
            .where(PhieuGiaoHang.du_lieu_sheet_id == ds.id)
            .order_by(PhieuGiaoHang.id.desc())
        )
        .scalars()
        .first()
    )
    if pgh is None:
        pgh = PhieuGiaoHang(
            du_lieu_sheet_id=ds.id,
            tai_khoan_vtp_id=None,
            ma_pgh_noi_bo=_sinh_ma_noi_bo(),
            trang_thai_pgh="cho_chot",
            nguoi_nhan_ten=(receiver or ds.ten_kh or "Khách"),
            nguoi_nhan_sdt=(receive_phone or ds.sdt_nguoi_nhan or ""),
            nguoi_nhan_dia_chi=(address or ds.dia_chi_nguoi_nhan or ""),
            hinh_thuc_tt=1,
            dich_vu_chinh="KHODEN",
        )
        session.add(pgh)

    pgh.kinkin_request_json = body if isinstance(body, (dict, list)) else None
    pgh.kinkin_response_json = (
        resp if isinstance(resp, (dict, list)) else ({"_raw": str(resp)[:2000]} if resp is not None else None)
    )
    pgh.kho_den_id = str(settings.DEFAULT_KHO_DEN_ID)
    # VTP nhúng trong cùng body/resp (1-call) → mirror sang cột vtp_* để chi_tiet.html hiển thị
    if co_vtp:
        pgh.vtp_request_json = pgh.kinkin_request_json
        pgh.vtp_response_json = pgh.kinkin_response_json

    if ok:
        pgh.trang_thai_kinkin = "da_tao"
        pgh.kinkin_tao_luc = _now()
        ma = _extract(resp, ("code", "soChungTu", "deliveryCode", "maPhieu", "id"))
        if ma:
            pgh.ma_pgh_kinkin = ma
        if co_vtp:
            mavtp = _extract(resp, ("partnerOrderNumber", "vtpOrderNumber", "orderNumber", "partnerCode"))
            if mavtp:
                pgh.ma_pgh_vtp = mavtp
                pgh.trang_thai_pgh = "da_chot"
                pgh.chot_luc = _now()
    else:
        pgh.trang_thai_kinkin = "loi_api_kinkin"
        pgh.kinkin_loi_message = (loi or "")[:1000]

    session.flush()
    return pgh
