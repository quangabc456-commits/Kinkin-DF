from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class DiaDanhTinh(Base):
    __tablename__ = "dia_danh_tinh"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    ma_tinh: Mapped[Optional[str]] = mapped_column(Text)
    ten_tinh: Mapped[str] = mapped_column(Text, nullable=False)
    tao_luc: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    huyen: Mapped[list["DiaDanhHuyen"]] = relationship(back_populates="tinh")

    __table_args__ = (Index("ix_dia_danh_tinh_ten", "ten_tinh"),)


class DiaDanhHuyen(Base):
    __tablename__ = "dia_danh_huyen"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    tinh_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("dia_danh_tinh.id", ondelete="CASCADE"), nullable=False
    )
    ma_huyen: Mapped[Optional[str]] = mapped_column(Text)
    ten_huyen: Mapped[str] = mapped_column(Text, nullable=False)
    la_dia_chi_moi: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    tao_luc: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    tinh: Mapped["DiaDanhTinh"] = relationship(back_populates="huyen")
    xa: Mapped[list["DiaDanhXa"]] = relationship(back_populates="huyen")

    __table_args__ = (Index("ix_dia_danh_huyen_ten_tinh", "ten_huyen", "tinh_id"),)


class DiaDanhXa(Base):
    __tablename__ = "dia_danh_xa"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    huyen_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("dia_danh_huyen.id", ondelete="CASCADE"), nullable=False
    )
    ten_xa: Mapped[str] = mapped_column(Text, nullable=False)
    tao_luc: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    huyen: Mapped["DiaDanhHuyen"] = relationship(back_populates="xa")

    __table_args__ = (Index("ix_dia_danh_xa_ten_huyen", "ten_xa", "huyen_id"),)
