from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, Boolean, Date, DateTime, Index, Integer, Numeric, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.phieu_giao_hang import PhieuGiaoHang


class DuLieuSheet(Base):
    __tablename__ = "du_lieu_sheet"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ten_sheet: Mapped[str] = mapped_column(Text, nullable=False)
    ngay_chot: Mapped[date] = mapped_column(Date, nullable=False)
    sheet_row_index: Mapped[int] = mapped_column(Integer, nullable=False)

    ma_kien_k: Mapped[Optional[str]] = mapped_column(Text)
    can_nang_kien_kg: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 3))
    ma_f_cha: Mapped[Optional[str]] = mapped_column(Text)
    ma_thung: Mapped[Optional[str]] = mapped_column(Text)
    ma_van_don: Mapped[str] = mapped_column(Text, nullable=False)
    can_nang_kg: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 3))
    phu_thu: Mapped[Optional[str]] = mapped_column(Text)
    ghi_chu: Mapped[Optional[str]] = mapped_column(Text)
    ten_kh: Mapped[Optional[str]] = mapped_column(Text)
    phuong_thuc_gui: Mapped[Optional[str]] = mapped_column(Text)
    thong_tin_gui_raw: Mapped[Optional[str]] = mapped_column(Text)
    nhom_san_pham: Mapped[Optional[str]] = mapped_column(Text)
    dia_chi_nguoi_nhan: Mapped[Optional[str]] = mapped_column(Text)
    sdt_nguoi_nhan: Mapped[Optional[str]] = mapped_column(Text)
    trang_thai_goc: Mapped[Optional[str]] = mapped_column(Text)
    ma_genkin: Mapped[Optional[str]] = mapped_column(Text)
    khoi_luong_genkin_kg: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 3))
    co_match_genkin: Mapped[Optional[bool]] = mapped_column(Boolean)

    dong_bo_lan_cuoi_luc: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    tao_luc: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    sua_luc: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    phieu_giao_hang: Mapped[list["PhieuGiaoHang"]] = relationship(back_populates="dong_sheet")

    __table_args__ = (
        UniqueConstraint("ma_van_don", name="uq_du_lieu_sheet_ma_van_don"),
        UniqueConstraint("ten_sheet", "sheet_row_index", name="uq_du_lieu_sheet_pos"),
        Index("ix_du_lieu_sheet_phuong_thuc_gui", "phuong_thuc_gui"),
        Index("ix_du_lieu_sheet_ngay_chot", "ngay_chot"),
        Index("ix_du_lieu_sheet_ten_kh", "ten_kh"),
        Index("ix_du_lieu_sheet_ma_kien_k", "ma_kien_k"),
        Index("ix_du_lieu_sheet_ma_f_cha", "ma_f_cha"),
        Index("ix_du_lieu_sheet_ma_thung", "ma_thung"),
    )
