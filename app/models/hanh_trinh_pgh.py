from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, Integer, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.phieu_giao_hang import PhieuGiaoHang


class HanhTrinhPgh(Base):
    __tablename__ = "hanh_trinh_pgh"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    phieu_giao_hang_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("phieu_giao_hang.id", ondelete="SET NULL")
    )
    ma_van_don_vtp: Mapped[str] = mapped_column(Text, nullable=False)
    ma_trang_thai: Mapped[int] = mapped_column(Integer, nullable=False)
    ten_trang_thai: Mapped[Optional[str]] = mapped_column(Text)
    thoi_gian_trang_thai: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    vi_tri_hien_tai: Mapped[Optional[str]] = mapped_column(Text)
    ghi_chu: Mapped[Optional[str]] = mapped_column(Text)
    nhan_vien_ten: Mapped[Optional[str]] = mapped_column(Text)
    nhan_vien_sdt: Mapped[Optional[str]] = mapped_column(Text)
    dang_chuyen_hoan: Mapped[Optional[bool]] = mapped_column(Boolean)
    ly_do_ma: Mapped[Optional[str]] = mapped_column(Text)
    pod_images_json: Mapped[Optional[dict]] = mapped_column(JSONB)
    payload_raw: Mapped[dict] = mapped_column(JSONB, nullable=False)

    tao_luc: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    pgh: Mapped[Optional["PhieuGiaoHang"]] = relationship(back_populates="hanh_trinh")

    __table_args__ = (
        UniqueConstraint(
            "ma_van_don_vtp",
            "ma_trang_thai",
            "thoi_gian_trang_thai",
            name="uq_hanh_trinh_pgh_unique_event",
        ),
        Index("ix_hanh_trinh_pgh_ma_van_don_vtp", "ma_van_don_vtp"),
        Index("ix_hanh_trinh_pgh_phieu_giao_hang_id", "phieu_giao_hang_id"),
    )
