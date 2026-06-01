from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import DiaDanhHuyen, DiaDanhTinh, DiaDanhXa


@dataclass
class KetQuaLookup:
    tinh_id: Optional[int]
    huyen_id: Optional[int]
    xa_id: Optional[int]
    tinh_ten: Optional[str]
    huyen_ten: Optional[str]
    xa_ten: Optional[str]


def _bo_dau(s: str) -> str:
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.replace("đ", "d").replace("Đ", "D")
    return s.lower().strip()


def _chuan_hoa(s: str) -> str:
    s = _bo_dau(s)
    s = re.sub(r"\b(thanh pho|tp\.?|tinh|quan|huyen|thi xa|phuong|xa|thi tran)\b", "", s)
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def parse_dia_chi(dia_chi: str) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """Tách tỉnh/huyện/xã từ chuỗi địa chỉ kiểu VTP."""
    parts = [p.strip() for p in dia_chi.split(",") if p.strip()]
    if len(parts) < 2:
        return None, None, None
    tinh = parts[-1] if len(parts) >= 1 else None
    huyen = parts[-2] if len(parts) >= 2 else None
    xa = parts[-3] if len(parts) >= 3 else None
    return tinh, huyen, xa


def lookup_dia_chi(session: Session, dia_chi: str) -> KetQuaLookup:
    tinh_s, huyen_s, xa_s = parse_dia_chi(dia_chi)
    tinh_row: Optional[DiaDanhTinh] = None
    huyen_row: Optional[DiaDanhHuyen] = None
    xa_row: Optional[DiaDanhXa] = None

    if tinh_s:
        key = _chuan_hoa(tinh_s)
        all_t = session.execute(select(DiaDanhTinh)).scalars().all()
        for t in all_t:
            if _chuan_hoa(t.ten_tinh) == key or key in _chuan_hoa(t.ten_tinh):
                tinh_row = t
                break

    if huyen_s and tinh_row is not None:
        key = _chuan_hoa(huyen_s)
        all_h = (
            session.execute(select(DiaDanhHuyen).where(DiaDanhHuyen.tinh_id == tinh_row.id))
            .scalars()
            .all()
        )
        for h in all_h:
            n = _chuan_hoa(h.ten_huyen)
            if n == key or key in n or n in key:
                huyen_row = h
                break

    if xa_s and huyen_row is not None:
        key = _chuan_hoa(xa_s)
        all_x = (
            session.execute(select(DiaDanhXa).where(DiaDanhXa.huyen_id == huyen_row.id))
            .scalars()
            .all()
        )
        for x in all_x:
            n = _chuan_hoa(x.ten_xa)
            if n == key or key in n or n in key:
                xa_row = x
                break

    return KetQuaLookup(
        tinh_id=tinh_row.id if tinh_row else None,
        huyen_id=huyen_row.id if huyen_row else None,
        xa_id=xa_row.id if xa_row else None,
        tinh_ten=tinh_row.ten_tinh if tinh_row else None,
        huyen_ten=huyen_row.ten_huyen if huyen_row else None,
        xa_ten=xa_row.ten_xa if xa_row else None,
    )
