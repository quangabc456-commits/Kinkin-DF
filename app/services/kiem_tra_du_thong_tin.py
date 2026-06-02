"""Kiểm tra dòng du_lieu_sheet đã đủ thông tin để tạo PGH chưa.

Worker gọi service này TRƯỚC khi gọi VTP/Kinkin API. Nếu thiếu trường nào,
worker tạo row phieu_giao_hang với trang_thai_pgh='cho_dien_thong_tin' +
thieu_truong_json=[...] để nhân viên vào UI điền.
"""
from __future__ import annotations

import re
from typing import Optional

from app.core.config import settings
from app.models import DuLieuSheet


_SDT_RE = re.compile(r"^0\d{9,10}$")


# (key, label hiển thị UI)
TRUONG_BAT_BUOC: list[tuple[str, str]] = [
    ("ten_kh", "Tên khách hàng"),
    ("sdt_nguoi_nhan", "SĐT người nhận"),
    ("dia_chi_nguoi_nhan", "Địa chỉ người nhận"),
    ("nhom_san_pham", "Nhóm sản phẩm"),
    ("can_nang_kg", "Cân nặng (kg)"),
]


def label_truong(key: str) -> str:
    for k, lb in TRUONG_BAT_BUOC:
        if k == key:
            return lb
    return key


def _chuan_hoa_sdt(s: Optional[str]) -> Optional[str]:
    if not s:
        return None
    s = re.sub(r"[^\d+]", "", s)
    if s.startswith("+84"):
        s = "0" + s[3:]
    elif s.startswith("84") and len(s) >= 11:
        s = "0" + s[2:]
    return s or None


def kiem_tra(dong: DuLieuSheet) -> list[str]:
    """Trả về list key các trường còn thiếu/không hợp lệ. Empty list = đủ thông tin."""
    thieu: list[str] = []

    if not (dong.ten_kh or "").strip():
        thieu.append("ten_kh")

    sdt = _chuan_hoa_sdt(dong.sdt_nguoi_nhan)
    if not sdt or not _SDT_RE.match(sdt):
        thieu.append("sdt_nguoi_nhan")

    dc = (dong.dia_chi_nguoi_nhan or "").strip()
    if len(dc) < settings.MIN_DIA_CHI_LEN:
        thieu.append("dia_chi_nguoi_nhan")

    if not (dong.nhom_san_pham or "").strip():
        thieu.append("nhom_san_pham")

    if dong.can_nang_kg is None or dong.can_nang_kg <= 0:
        thieu.append("can_nang_kg")

    return thieu
