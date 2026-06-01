from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, Boolean, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.phieu_giao_hang import PhieuGiaoHang


class TaiKhoanVtp(Base):
    __tablename__ = "tai_khoan_vtp"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ten_hien_thi: Mapped[str] = mapped_column(Text, nullable=False)
    username: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    password_enc: Mapped[Optional[str]] = mapped_column(Text)
    secret_token: Mapped[Optional[str]] = mapped_column(Text)
    token_hien_tai: Mapped[Optional[str]] = mapped_column(Text)
    token_het_han_luc: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    webhook_secret: Mapped[Optional[str]] = mapped_column(Text)
    mac_dinh: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    kich_hoat: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    moi_truong: Mapped[str] = mapped_column(
        Text, nullable=False, default="production", server_default="production"
    )

    tao_luc: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    sua_luc: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    phieu_giao_hang: Mapped[list["PhieuGiaoHang"]] = relationship(back_populates="tai_khoan_vtp")
