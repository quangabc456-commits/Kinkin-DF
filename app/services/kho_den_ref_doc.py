"""Đọc reference kho đến từ DB cache (bảng kd_*) — KHÔNG call live, nhanh & không cần token.

Dùng cho màn hình tạo PGH: tra khách (theo tên/mã/sđt), địa chỉ đã có của khách, tỉnh, kho.
Kiện F KHÔNG ở đây — F volatile nên giữ live (khoden_client.ds_kien_f).

Trả về dict có KEY GIỐNG response live (id/code/name/phone, receiver/wardName...) để template
và service tạo PGH dùng chung, không phải sửa chỗ khác.
"""
from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.kho_den_ref import KdDiaChiGiao, KdKhachHang, KdKho, KdTinh


def _khach_dict(k: KdKhachHang) -> dict[str, Any]:
    return {
        "id": k.customer_id,
        "code": k.code,
        "name": k.name,
        "phone": k.phone,
        "groupName": k.group_name,
        "paymentType": k.payment_type,
        "isParent": k.is_parent,
    }


def tim_khach(session: Session, term: str, limit: int = 25) -> list[dict[str, Any]]:
    """Tìm khách trong kd_khach_hang theo mã / tên / SĐT (ILIKE). Ưu tiên khớp mã chính xác."""
    term = (term or "").strip()
    if not term:
        return []
    like = f"%{term}%"
    rows = (
        session.execute(
            select(KdKhachHang)
            .where(
                or_(
                    KdKhachHang.code.ilike(like),
                    KdKhachHang.name.ilike(like),
                    KdKhachHang.phone.ilike(like),
                )
            )
            .order_by(
                # khớp mã chính xác lên đầu, rồi theo mã
                (func.upper(KdKhachHang.code) == term.upper()).desc(),
                KdKhachHang.code.asc(),
            )
            .limit(limit)
        )
        .scalars()
        .all()
    )
    return [_khach_dict(k) for k in rows]


def lay_khach_theo_code(session: Session, code: str) -> Optional[dict[str, Any]]:
    """Khớp CHÍNH XÁC theo mã khách (không phân biệt hoa/thường). None nếu không có."""
    code = (code or "").strip()
    if not code:
        return None
    k = (
        session.execute(
            select(KdKhachHang).where(func.upper(KdKhachHang.code) == code.upper())
        )
        .scalars()
        .first()
    )
    return _khach_dict(k) if k else None


def _dia_chi_dict(d: KdDiaChiGiao) -> dict[str, Any]:
    return {
        "id": d.address_id,
        "customerId": d.customer_id,
        "receiver": d.receiver,
        "phone": d.phone,
        "nationId": d.nation_id,
        "nationName": d.nation_name,
        "provinceId": d.province_id,
        "provinceName": d.province_name,
        "districtId": d.district_id,
        "districtName": d.district_name,
        "wardId": d.ward_id,
        "wardName": d.ward_name,
        "address": d.address,
    }


def dia_chi_cua_khach(session: Session, customer_id: str) -> list[dict[str, Any]]:
    """Địa chỉ giao đã có của khách (theo customerId GUID) từ kd_dia_chi_giao."""
    if not customer_id:
        return []
    rows = (
        session.execute(
            select(KdDiaChiGiao)
            .where(KdDiaChiGiao.customer_id == customer_id)
            .order_by(KdDiaChiGiao.receiver.asc())
        )
        .scalars()
        .all()
    )
    return [_dia_chi_dict(d) for d in rows]


def ds_tinh(session: Session) -> list[dict[str, Any]]:
    """Danh sách tỉnh từ kd_tinh (cho datalist gợi ý ở luồng địa chỉ mới)."""
    rows = (
        session.execute(select(KdTinh).order_by(KdTinh.name.asc())).scalars().all()
    )
    return [{"id": t.id, "name": t.name, "code": t.code} for t in rows]


def ds_kho(session: Session) -> list[dict[str, Any]]:
    """Danh sách kho từ kd_kho."""
    rows = session.execute(select(KdKho).order_by(KdKho.name.asc())).scalars().all()
    return [{"id": k.id, "kinkinId": k.kinkin_id, "name": k.name, "code": k.code} for k in rows]
