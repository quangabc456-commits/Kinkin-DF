from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class LogDongBoSheet(Base):
    __tablename__ = "log_dong_bo_sheet"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ten_sheet: Mapped[str] = mapped_column(Text, nullable=False)
    bat_dau_luc: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    ket_thuc_luc: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    so_dong_doc: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    so_dong_them_moi: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    so_dong_cap_nhat: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    so_dong_loi: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    chi_tiet_loi: Mapped[Optional[list]] = mapped_column(JSONB)
    trang_thai: Mapped[str] = mapped_column(Text, default="dang_chay", server_default="dang_chay")


class LogApiVtp(Base):
    __tablename__ = "log_api_vtp"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    endpoint: Mapped[str] = mapped_column(Text, nullable=False)
    method: Mapped[str] = mapped_column(Text, nullable=False)
    request_body: Mapped[Optional[dict]] = mapped_column(JSONB)
    response_body: Mapped[Optional[dict]] = mapped_column(JSONB)
    http_status: Mapped[Optional[int]] = mapped_column(Integer)
    loi_message: Mapped[Optional[str]] = mapped_column(Text)
    phieu_giao_hang_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("phieu_giao_hang.id", ondelete="SET NULL")
    )
    tai_khoan_vtp_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("tai_khoan_vtp.id", ondelete="SET NULL")
    )
    thoi_gian: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CauHinh(Base):
    __tablename__ = "cau_hinh"

    khoa: Mapped[str] = mapped_column(Text, primary_key=True)
    gia_tri: Mapped[Optional[str]] = mapped_column(Text)
    mo_ta: Mapped[Optional[str]] = mapped_column(Text)
    sua_luc: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())
