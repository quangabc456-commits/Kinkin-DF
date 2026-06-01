from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class TaiKhoanKinkin(Base):
    __tablename__ = "tai_khoan_kinkin"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ten_hien_thi: Mapped[str] = mapped_column(Text, nullable=False)
    username: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    password_enc: Mapped[Optional[str]] = mapped_column(Text)

    warehouse_id: Mapped[Optional[str]] = mapped_column(Text)
    customer_code: Mapped[Optional[str]] = mapped_column(Text)
    package_k_apikey: Mapped[Optional[str]] = mapped_column(Text)

    token_hien_tai: Mapped[Optional[str]] = mapped_column(Text)
    token_het_han_luc: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    base_identity: Mapped[str] = mapped_column(
        Text, default="https://identityapi.vanchuyenkinkin.com", server_default="https://identityapi.vanchuyenkinkin.com"
    )
    base_export: Mapped[str] = mapped_column(
        Text, default="https://warehouseexportapi.vanchuyenkinkin.com", server_default="https://warehouseexportapi.vanchuyenkinkin.com"
    )
    base_departure: Mapped[str] = mapped_column(
        Text, default="https://warehousedepartureapi.vanchuyenkinkin.com", server_default="https://warehousedepartureapi.vanchuyenkinkin.com"
    )

    mac_dinh: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    kich_hoat: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    tao_luc: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    sua_luc: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())
