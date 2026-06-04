"""Cache reference data hệ KHO ĐẾN (*.vanchuyenkinkin.com) về DB.

Màn hình tạo PGH đọc từ các bảng `kd_*` này (nhanh, ổn định) thay vì call live mỗi lần.
Sync bằng app/services/kho_den_ref_sync.py. Mỗi bảng có `host_origin` ('that'|'test')
để chứa song song dữ liệu 2 môi trường nếu cần.

PK = GUID/id gốc từ API (Text) để upsert on_conflict gọn (trừ kd_sync_log = surrogate).
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import BigInteger, Boolean, DateTime, Index, Integer, Numeric, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class KdKhachHang(Base):
    """Khách hàng kho đến (chủ kiện F = khách Kinkin). Nguồn: customer/get-list."""

    __tablename__ = "kd_khach_hang"

    customer_id: Mapped[str] = mapped_column(Text, primary_key=True)  # GUID
    kinkin_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    code: Mapped[Optional[str]] = mapped_column(Text)  # customerCode, vd 093HN-VAT
    name: Mapped[Optional[str]] = mapped_column(Text)
    phone: Mapped[Optional[str]] = mapped_column(Text)
    address: Mapped[Optional[str]] = mapped_column(Text)
    payment_type: Mapped[Optional[int]] = mapped_column(Integer)
    group_name: Mapped[Optional[str]] = mapped_column(Text)
    parent_id: Mapped[Optional[str]] = mapped_column(Text)
    is_parent: Mapped[Optional[bool]] = mapped_column(Boolean)
    payload_raw: Mapped[Optional[Any]] = mapped_column(JSONB)
    host_origin: Mapped[str] = mapped_column(Text, default="that", server_default="that")
    last_sync_luc: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    tao_luc: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    sua_luc: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        Index("ix_kd_khach_hang_code", "code"),
        Index("ix_kd_khach_hang_host", "host_origin"),
    )


class KdDiaChiGiao(Base):
    """Địa chỉ giao đã có của khách (luồng 'địa chỉ cũ'). Nguồn: deliveryAddress/get-list."""

    __tablename__ = "kd_dia_chi_giao"

    address_id: Mapped[str] = mapped_column(Text, primary_key=True)  # GUID
    type_id: Mapped[Optional[int]] = mapped_column(Integer)
    customer_id: Mapped[Optional[str]] = mapped_column(Text)
    customer_code: Mapped[Optional[str]] = mapped_column(Text)
    receiver: Mapped[Optional[str]] = mapped_column(Text)
    phone: Mapped[Optional[str]] = mapped_column(Text)
    nation_id: Mapped[Optional[str]] = mapped_column(Text)
    nation_name: Mapped[Optional[str]] = mapped_column(Text)
    province_id: Mapped[Optional[str]] = mapped_column(Text)
    province_name: Mapped[Optional[str]] = mapped_column(Text)
    district_id: Mapped[Optional[str]] = mapped_column(Text)
    district_name: Mapped[Optional[str]] = mapped_column(Text)
    ward_id: Mapped[Optional[str]] = mapped_column(Text)
    ward_name: Mapped[Optional[str]] = mapped_column(Text)
    address: Mapped[Optional[str]] = mapped_column(Text)
    delivery_point_code: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean)
    payload_raw: Mapped[Optional[Any]] = mapped_column(JSONB)
    host_origin: Mapped[str] = mapped_column(Text, default="that", server_default="that")
    last_sync_luc: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    tao_luc: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    sua_luc: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        Index("ix_kd_dia_chi_giao_customer_id", "customer_id"),
        Index("ix_kd_dia_chi_giao_customer_code", "customer_code"),
    )


class KdNation(Base):
    __tablename__ = "kd_nation"
    id: Mapped[str] = mapped_column(Text, primary_key=True)  # GUID
    name: Mapped[Optional[str]] = mapped_column(Text)
    host_origin: Mapped[str] = mapped_column(Text, default="that", server_default="that")
    tao_luc: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class KdTinh(Base):
    __tablename__ = "kd_tinh"
    id: Mapped[str] = mapped_column(Text, primary_key=True)  # GUID
    nation_id: Mapped[Optional[str]] = mapped_column(Text)
    name: Mapped[Optional[str]] = mapped_column(Text)
    code: Mapped[Optional[str]] = mapped_column(Text)
    name_norm: Mapped[Optional[str]] = mapped_column(Text)
    host_origin: Mapped[str] = mapped_column(Text, default="that", server_default="that")
    tao_luc: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (Index("ix_kd_tinh_norm", "name_norm"), Index("ix_kd_tinh_nation", "nation_id"))


class KdHuyen(Base):
    __tablename__ = "kd_huyen"
    id: Mapped[str] = mapped_column(Text, primary_key=True)  # GUID
    province_id: Mapped[Optional[str]] = mapped_column(Text)
    name: Mapped[Optional[str]] = mapped_column(Text)
    code: Mapped[Optional[str]] = mapped_column(Text)
    name_norm: Mapped[Optional[str]] = mapped_column(Text)
    host_origin: Mapped[str] = mapped_column(Text, default="that", server_default="that")
    tao_luc: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (Index("ix_kd_huyen_province", "province_id"), Index("ix_kd_huyen_norm", "name_norm"))


class KdXa(Base):
    __tablename__ = "kd_xa"
    id: Mapped[str] = mapped_column(Text, primary_key=True)  # GUID
    district_id: Mapped[Optional[str]] = mapped_column(Text)
    name: Mapped[Optional[str]] = mapped_column(Text)
    code: Mapped[Optional[str]] = mapped_column(Text)
    name_norm: Mapped[Optional[str]] = mapped_column(Text)
    host_origin: Mapped[str] = mapped_column(Text, default="that", server_default="that")
    tao_luc: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (Index("ix_kd_xa_district", "district_id"), Index("ix_kd_xa_norm", "name_norm"))


class KdKienF(Base):
    """Kiện F (để chọn lên PGH). Volatile. Nguồn: packageF/common/get-list-paginate."""

    __tablename__ = "kd_kien_f"

    package_f_id: Mapped[str] = mapped_column(Text, primary_key=True)  # GUID
    package_f_code: Mapped[Optional[str]] = mapped_column(Text)  # = codeTracking
    package_f_name: Mapped[Optional[str]] = mapped_column(Text)  # F…
    customer_code: Mapped[Optional[str]] = mapped_column(Text)
    warehouse_id: Mapped[Optional[str]] = mapped_column(Text)
    current_status: Mapped[Optional[int]] = mapped_column(Integer)
    status_name: Mapped[Optional[str]] = mapped_column(Text)
    weight: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 3))
    mawb: Mapped[Optional[str]] = mapped_column(Text)
    code_tracking: Mapped[Optional[str]] = mapped_column(Text)
    payload_raw: Mapped[Optional[Any]] = mapped_column(JSONB)
    host_origin: Mapped[str] = mapped_column(Text, default="that", server_default="that")
    last_sync_luc: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    tao_luc: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    sua_luc: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        Index("ix_kd_kien_f_code", "package_f_code"),
        Index("ix_kd_kien_f_name", "package_f_name"),
        Index("ix_kd_kien_f_customer", "customer_code"),
    )


class KdKienK(Base):
    """Kiện K (tra Ma kien K → F con). Nguồn: packageK/common/get-list-paginate.

    LƯU Ý: chưa có luồng sync bulk — kiện K hiện tra cứu ON-DEMAND qua
    khoden_client.tim_k_theo_thong_tin (get-packageK-by-information). Bảng này giữ chỗ
    cho luồng cache bulk tương lai (thêm sync_kien_k khi cần).
    """

    __tablename__ = "kd_kien_k"

    package_k_id: Mapped[str] = mapped_column(Text, primary_key=True)  # GUID
    package_k_code: Mapped[Optional[str]] = mapped_column(Text)
    package_k_name: Mapped[Optional[str]] = mapped_column(Text)
    customer_code: Mapped[Optional[str]] = mapped_column(Text)
    warehouse_id: Mapped[Optional[str]] = mapped_column(Text)
    current_status: Mapped[Optional[int]] = mapped_column(Integer)
    status_name: Mapped[Optional[str]] = mapped_column(Text)
    weight: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 3))
    payload_raw: Mapped[Optional[Any]] = mapped_column(JSONB)
    host_origin: Mapped[str] = mapped_column(Text, default="that", server_default="that")
    last_sync_luc: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    tao_luc: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    sua_luc: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        Index("ix_kd_kien_k_code", "package_k_code"),
        Index("ix_kd_kien_k_customer", "customer_code"),
    )


class KdKho(Base):
    __tablename__ = "kd_kho"
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    kinkin_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    name: Mapped[Optional[str]] = mapped_column(Text)
    code: Mapped[Optional[str]] = mapped_column(Text)
    host_origin: Mapped[str] = mapped_column(Text, default="that", server_default="that")
    tao_luc: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class KdSyncLog(Base):
    __tablename__ = "kd_sync_log"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    bang: Mapped[str] = mapped_column(Text, nullable=False)
    endpoint: Mapped[Optional[str]] = mapped_column(Text)
    host_origin: Mapped[Optional[str]] = mapped_column(Text)
    bat_dau_luc: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    ket_thuc_luc: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    so_doc: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    them_moi: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    cap_nhat: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    so_loi: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    trang_thai: Mapped[Optional[str]] = mapped_column(Text)
    chi_tiet_loi: Mapped[Optional[str]] = mapped_column(Text)
    tao_luc: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (Index("ix_kd_sync_log_bang", "bang"),)
