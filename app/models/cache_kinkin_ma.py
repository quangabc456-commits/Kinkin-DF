from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import BigInteger, DateTime, Index, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class CacheKinkinMa(Base):
    """Cache thông tin Kinkin cho 1 mã (GKA/F/K/VK/PGH).

    Worker cron refresh row này; UI lookup chỉ đọc từ bảng này, KHÔNG call API live.
    """

    __tablename__ = "cache_kinkin_ma"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    loai: Mapped[Optional[str]] = mapped_column(Text)

    ma_don_chinh: Mapped[Optional[str]] = mapped_column(Text)
    bill_code: Mapped[Optional[str]] = mapped_column(Text)
    trang_thai: Mapped[Optional[str]] = mapped_column(Text)
    ten_kho: Mapped[Optional[str]] = mapped_column(Text)
    warehouse_id: Mapped[Optional[str]] = mapped_column(Text)

    ma_kien_k: Mapped[Optional[str]] = mapped_column(Text)
    ma_f_cha: Mapped[Optional[str]] = mapped_column(Text)
    ma_thung: Mapped[Optional[str]] = mapped_column(Text)

    nguoi_nhan: Mapped[Optional[str]] = mapped_column(Text)
    sdt_nguoi_nhan: Mapped[Optional[str]] = mapped_column(Text)
    dia_chi_nhan: Mapped[Optional[str]] = mapped_column(Text)

    nha_van_chuyen: Mapped[Optional[str]] = mapped_column(Text)
    so_luong: Mapped[Optional[int]] = mapped_column(BigInteger)
    tong_tien_vnd: Mapped[Optional[int]] = mapped_column(BigInteger)

    ngay_tao_kinkin: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    ngay_cap_nhat_kinkin: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    payload_raw: Mapped[Optional[Any]] = mapped_column(JSONB)

    last_sync_luc: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_sync_loi: Mapped[Optional[str]] = mapped_column(Text)

    tao_luc: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    sua_luc: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        Index("ix_cache_kinkin_ma_loai", "loai"),
        Index("ix_cache_kinkin_ma_last_sync", "last_sync_luc"),
        Index("ix_cache_kinkin_ma_bill_code", "bill_code"),
    )
