from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, Integer, Numeric, SmallInteger, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.du_lieu_sheet import DuLieuSheet
    from app.models.hanh_trinh_pgh import HanhTrinhPgh
    from app.models.tai_khoan_vtp import TaiKhoanVtp


class PhieuGiaoHang(Base):
    __tablename__ = "phieu_giao_hang"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    du_lieu_sheet_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("du_lieu_sheet.id", ondelete="RESTRICT"), nullable=False
    )
    tai_khoan_vtp_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("tai_khoan_vtp.id", ondelete="RESTRICT"), nullable=True
    )

    ma_pgh_vtp: Mapped[Optional[str]] = mapped_column(Text, unique=True)
    ma_pgh_noi_bo: Mapped[Optional[str]] = mapped_column(Text)
    trang_thai_pgh: Mapped[str] = mapped_column(
        Text, nullable=False, default="cho_chot", server_default="cho_chot"
    )

    nguoi_nhan_ten: Mapped[str] = mapped_column(Text, nullable=False)
    nguoi_nhan_sdt: Mapped[str] = mapped_column(Text, nullable=False)
    nguoi_nhan_dia_chi: Mapped[str] = mapped_column(Text, nullable=False)
    nguoi_nhan_tinh_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    nguoi_nhan_huyen_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    nguoi_nhan_xa_id: Mapped[Optional[int]] = mapped_column(BigInteger)

    san_pham_ten: Mapped[Optional[str]] = mapped_column(Text)
    san_pham_so_luong: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    san_pham_gia_vnd: Mapped[int] = mapped_column(BigInteger, default=0, server_default="0")
    san_pham_can_nang_gram: Mapped[Optional[int]] = mapped_column(BigInteger)
    san_pham_dai_cm: Mapped[Optional[int]] = mapped_column(Integer)
    san_pham_rong_cm: Mapped[Optional[int]] = mapped_column(Integer)
    san_pham_cao_cm: Mapped[Optional[int]] = mapped_column(Integer)

    loai_hang: Mapped[str] = mapped_column(Text, default="HH", server_default="HH")
    hinh_thuc_tt: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    dich_vu_chinh: Mapped[str] = mapped_column(Text, nullable=False)
    dich_vu_cong_them: Mapped[Optional[str]] = mapped_column(Text)
    tien_thu_ho_vnd: Mapped[int] = mapped_column(BigInteger, default=0, server_default="0")
    tien_xem_hang_vnd: Mapped[int] = mapped_column(BigInteger, default=0, server_default="0")
    ghi_chu_pgh: Mapped[Optional[str]] = mapped_column(Text)
    sort_code: Mapped[Optional[str]] = mapped_column(Text)

    cuoc_tong_vnd: Mapped[Optional[int]] = mapped_column(BigInteger)
    cuoc_chinh_vnd: Mapped[Optional[int]] = mapped_column(BigInteger)
    phi_xang_dau_vnd: Mapped[Optional[int]] = mapped_column(BigInteger)
    phi_thu_ho_vnd: Mapped[Optional[int]] = mapped_column(BigInteger)
    phi_khac_vnd: Mapped[Optional[int]] = mapped_column(BigInteger)
    vat_vnd: Mapped[Optional[int]] = mapped_column(BigInteger)
    kpi_giao_gio: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2))
    can_quy_doi_gram: Mapped[Optional[int]] = mapped_column(BigInteger)

    vtp_request_json: Mapped[Optional[dict]] = mapped_column(JSONB)
    vtp_response_json: Mapped[Optional[dict]] = mapped_column(JSONB)
    loi_message: Mapped[Optional[str]] = mapped_column(Text)
    da_ghi_lai_sheet: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )

    chot_luc: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    chot_boi: Mapped[Optional[str]] = mapped_column(Text)
    tao_luc: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    sua_luc: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    ma_pgh_kinkin: Mapped[Optional[str]] = mapped_column(Text, unique=True)
    kho_den_id: Mapped[Optional[str]] = mapped_column(Text)
    trang_thai_kinkin: Mapped[str] = mapped_column(
        Text, nullable=False, default="chua_tao", server_default="chua_tao"
    )
    kinkin_request_json: Mapped[Optional[dict]] = mapped_column(JSONB)
    kinkin_response_json: Mapped[Optional[dict]] = mapped_column(JSONB)
    kinkin_loi_message: Mapped[Optional[str]] = mapped_column(Text)
    kinkin_tao_luc: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    thieu_truong_json: Mapped[Optional[list]] = mapped_column(JSONB)

    dong_sheet: Mapped["DuLieuSheet"] = relationship(back_populates="phieu_giao_hang")
    tai_khoan_vtp: Mapped[Optional["TaiKhoanVtp"]] = relationship(back_populates="phieu_giao_hang")
    hanh_trinh: Mapped[list["HanhTrinhPgh"]] = relationship(back_populates="pgh")

    __table_args__ = (
        Index("ix_phieu_giao_hang_trang_thai", "trang_thai_pgh"),
        Index("ix_phieu_giao_hang_ma_pgh_vtp", "ma_pgh_vtp"),
        Index("ix_phieu_giao_hang_du_lieu_sheet_id", "du_lieu_sheet_id"),
        Index("ix_phieu_giao_hang_trang_thai_kinkin", "trang_thai_kinkin"),
    )
