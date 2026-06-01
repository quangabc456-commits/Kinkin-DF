"""initial schema: 8 bang chinh

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-28

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB


revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "du_lieu_sheet",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("ten_sheet", sa.Text(), nullable=False),
        sa.Column("ngay_chot", sa.Date(), nullable=False),
        sa.Column("sheet_row_index", sa.Integer(), nullable=False),
        sa.Column("ma_kien_k", sa.Text()),
        sa.Column("can_nang_kien_kg", sa.Numeric(10, 3)),
        sa.Column("ma_f_cha", sa.Text()),
        sa.Column("ma_thung", sa.Text()),
        sa.Column("ma_van_don", sa.Text(), nullable=False),
        sa.Column("can_nang_kg", sa.Numeric(10, 3)),
        sa.Column("phu_thu", sa.Text()),
        sa.Column("ghi_chu", sa.Text()),
        sa.Column("ten_kh", sa.Text()),
        sa.Column("phuong_thuc_gui", sa.Text()),
        sa.Column("thong_tin_gui_raw", sa.Text()),
        sa.Column("nhom_san_pham", sa.Text()),
        sa.Column("dia_chi_nguoi_nhan", sa.Text()),
        sa.Column("sdt_nguoi_nhan", sa.Text()),
        sa.Column("trang_thai_goc", sa.Text()),
        sa.Column("ma_genkin", sa.Text()),
        sa.Column("khoi_luong_genkin_kg", sa.Numeric(10, 3)),
        sa.Column("co_match_genkin", sa.Boolean()),
        sa.Column("dong_bo_lan_cuoi_luc", sa.DateTime(timezone=True)),
        sa.Column("tao_luc", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("sua_luc", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("ma_van_don", name="uq_du_lieu_sheet_ma_van_don"),
        sa.UniqueConstraint("ten_sheet", "sheet_row_index", name="uq_du_lieu_sheet_pos"),
    )
    op.create_index("ix_du_lieu_sheet_phuong_thuc_gui", "du_lieu_sheet", ["phuong_thuc_gui"])
    op.create_index("ix_du_lieu_sheet_ngay_chot", "du_lieu_sheet", ["ngay_chot"])
    op.create_index("ix_du_lieu_sheet_ten_kh", "du_lieu_sheet", ["ten_kh"])
    op.create_index("ix_du_lieu_sheet_ma_kien_k", "du_lieu_sheet", ["ma_kien_k"])
    op.create_index("ix_du_lieu_sheet_ma_f_cha", "du_lieu_sheet", ["ma_f_cha"])
    op.create_index("ix_du_lieu_sheet_ma_thung", "du_lieu_sheet", ["ma_thung"])

    op.create_table(
        "tai_khoan_vtp",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("ten_hien_thi", sa.Text(), nullable=False),
        sa.Column("username", sa.Text(), nullable=False, unique=True),
        sa.Column("password_enc", sa.Text()),
        sa.Column("secret_token", sa.Text()),
        sa.Column("token_hien_tai", sa.Text()),
        sa.Column("token_het_han_luc", sa.DateTime(timezone=True)),
        sa.Column("webhook_secret", sa.Text()),
        sa.Column("mac_dinh", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("kich_hoat", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("moi_truong", sa.Text(), nullable=False, server_default="production"),
        sa.Column("tao_luc", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("sua_luc", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "phieu_giao_hang",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "du_lieu_sheet_id",
            sa.BigInteger(),
            sa.ForeignKey("du_lieu_sheet.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "tai_khoan_vtp_id",
            sa.BigInteger(),
            sa.ForeignKey("tai_khoan_vtp.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("ma_pgh_vtp", sa.Text(), unique=True),
        sa.Column("ma_pgh_noi_bo", sa.Text()),
        sa.Column("trang_thai_pgh", sa.Text(), nullable=False, server_default="cho_chot"),
        sa.Column("nguoi_nhan_ten", sa.Text(), nullable=False),
        sa.Column("nguoi_nhan_sdt", sa.Text(), nullable=False),
        sa.Column("nguoi_nhan_dia_chi", sa.Text(), nullable=False),
        sa.Column("nguoi_nhan_tinh_id", sa.BigInteger()),
        sa.Column("nguoi_nhan_huyen_id", sa.BigInteger()),
        sa.Column("nguoi_nhan_xa_id", sa.BigInteger()),
        sa.Column("san_pham_ten", sa.Text()),
        sa.Column("san_pham_so_luong", sa.Integer(), server_default="1"),
        sa.Column("san_pham_gia_vnd", sa.BigInteger(), server_default="0"),
        sa.Column("san_pham_can_nang_gram", sa.BigInteger()),
        sa.Column("san_pham_dai_cm", sa.Integer()),
        sa.Column("san_pham_rong_cm", sa.Integer()),
        sa.Column("san_pham_cao_cm", sa.Integer()),
        sa.Column("loai_hang", sa.Text(), server_default="HH"),
        sa.Column("hinh_thuc_tt", sa.SmallInteger(), nullable=False),
        sa.Column("dich_vu_chinh", sa.Text(), nullable=False),
        sa.Column("dich_vu_cong_them", sa.Text()),
        sa.Column("tien_thu_ho_vnd", sa.BigInteger(), server_default="0"),
        sa.Column("tien_xem_hang_vnd", sa.BigInteger(), server_default="0"),
        sa.Column("ghi_chu_pgh", sa.Text()),
        sa.Column("sort_code", sa.Text()),
        sa.Column("cuoc_tong_vnd", sa.BigInteger()),
        sa.Column("cuoc_chinh_vnd", sa.BigInteger()),
        sa.Column("phi_xang_dau_vnd", sa.BigInteger()),
        sa.Column("phi_thu_ho_vnd", sa.BigInteger()),
        sa.Column("phi_khac_vnd", sa.BigInteger()),
        sa.Column("vat_vnd", sa.BigInteger()),
        sa.Column("kpi_giao_gio", sa.Numeric(6, 2)),
        sa.Column("can_quy_doi_gram", sa.BigInteger()),
        sa.Column("vtp_request_json", JSONB()),
        sa.Column("vtp_response_json", JSONB()),
        sa.Column("loi_message", sa.Text()),
        sa.Column("da_ghi_lai_sheet", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("chot_luc", sa.DateTime(timezone=True)),
        sa.Column("chot_boi", sa.Text()),
        sa.Column("tao_luc", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("sua_luc", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_phieu_giao_hang_trang_thai", "phieu_giao_hang", ["trang_thai_pgh"])
    op.create_index("ix_phieu_giao_hang_ma_pgh_vtp", "phieu_giao_hang", ["ma_pgh_vtp"])
    op.create_index("ix_phieu_giao_hang_du_lieu_sheet_id", "phieu_giao_hang", ["du_lieu_sheet_id"])

    op.create_table(
        "hanh_trinh_pgh",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "phieu_giao_hang_id",
            sa.BigInteger(),
            sa.ForeignKey("phieu_giao_hang.id", ondelete="SET NULL"),
        ),
        sa.Column("ma_van_don_vtp", sa.Text(), nullable=False),
        sa.Column("ma_trang_thai", sa.Integer(), nullable=False),
        sa.Column("ten_trang_thai", sa.Text()),
        sa.Column("thoi_gian_trang_thai", sa.DateTime(timezone=True), nullable=False),
        sa.Column("vi_tri_hien_tai", sa.Text()),
        sa.Column("ghi_chu", sa.Text()),
        sa.Column("nhan_vien_ten", sa.Text()),
        sa.Column("nhan_vien_sdt", sa.Text()),
        sa.Column("dang_chuyen_hoan", sa.Boolean()),
        sa.Column("ly_do_ma", sa.Text()),
        sa.Column("pod_images_json", JSONB()),
        sa.Column("payload_raw", JSONB(), nullable=False),
        sa.Column("tao_luc", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint(
            "ma_van_don_vtp",
            "ma_trang_thai",
            "thoi_gian_trang_thai",
            name="uq_hanh_trinh_pgh_unique_event",
        ),
    )
    op.create_index("ix_hanh_trinh_pgh_ma_van_don_vtp", "hanh_trinh_pgh", ["ma_van_don_vtp"])
    op.create_index("ix_hanh_trinh_pgh_phieu_giao_hang_id", "hanh_trinh_pgh", ["phieu_giao_hang_id"])

    op.create_table(
        "dia_danh_tinh",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=False),
        sa.Column("ma_tinh", sa.Text()),
        sa.Column("ten_tinh", sa.Text(), nullable=False),
        sa.Column("tao_luc", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_dia_danh_tinh_ten", "dia_danh_tinh", ["ten_tinh"])

    op.create_table(
        "dia_danh_huyen",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=False),
        sa.Column(
            "tinh_id",
            sa.BigInteger(),
            sa.ForeignKey("dia_danh_tinh.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("ma_huyen", sa.Text()),
        sa.Column("ten_huyen", sa.Text(), nullable=False),
        sa.Column("la_dia_chi_moi", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("tao_luc", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_dia_danh_huyen_ten_tinh", "dia_danh_huyen", ["ten_huyen", "tinh_id"])

    op.create_table(
        "dia_danh_xa",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=False),
        sa.Column(
            "huyen_id",
            sa.BigInteger(),
            sa.ForeignKey("dia_danh_huyen.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("ten_xa", sa.Text(), nullable=False),
        sa.Column("tao_luc", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_dia_danh_xa_ten_huyen", "dia_danh_xa", ["ten_xa", "huyen_id"])

    op.create_table(
        "log_dong_bo_sheet",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("ten_sheet", sa.Text(), nullable=False),
        sa.Column("bat_dau_luc", sa.DateTime(timezone=True)),
        sa.Column("ket_thuc_luc", sa.DateTime(timezone=True)),
        sa.Column("so_dong_doc", sa.Integer(), server_default="0"),
        sa.Column("so_dong_them_moi", sa.Integer(), server_default="0"),
        sa.Column("so_dong_cap_nhat", sa.Integer(), server_default="0"),
        sa.Column("so_dong_loi", sa.Integer(), server_default="0"),
        sa.Column("chi_tiet_loi", JSONB()),
        sa.Column("trang_thai", sa.Text(), server_default="dang_chay"),
    )

    op.create_table(
        "log_api_vtp",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("endpoint", sa.Text(), nullable=False),
        sa.Column("method", sa.Text(), nullable=False),
        sa.Column("request_body", JSONB()),
        sa.Column("response_body", JSONB()),
        sa.Column("http_status", sa.Integer()),
        sa.Column("loi_message", sa.Text()),
        sa.Column(
            "phieu_giao_hang_id",
            sa.BigInteger(),
            sa.ForeignKey("phieu_giao_hang.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "tai_khoan_vtp_id",
            sa.BigInteger(),
            sa.ForeignKey("tai_khoan_vtp.id", ondelete="SET NULL"),
        ),
        sa.Column("thoi_gian", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "cau_hinh",
        sa.Column("khoa", sa.Text(), primary_key=True),
        sa.Column("gia_tri", sa.Text()),
        sa.Column("mo_ta", sa.Text()),
        sa.Column("sua_luc", sa.DateTime(timezone=True)),
    )

    op.execute(
        """
        INSERT INTO cau_hinh (khoa, gia_tri, mo_ta) VALUES
        ('SHEET_ID', '1S9FtklMhj6rKZmrtYx3jIKBz_xEDNrNYST0khlb1rB0', 'Google Sheet 450HN-GENKIN'),
        ('VTP_BASE_URL', 'https://partnerdev.viettelpost.vn', 'Base URL VTP partner'),
        ('DEFAULT_ORDER_SERVICE', 'VCN', 'Mã dịch vụ chính mặc định khi tạo PGH'),
        ('DEFAULT_ORDER_PAYMENT', '1', '1=khong thu ho, 2=thu cuoc+hang, 3=thu hang, 4=thu cuoc')
        """
    )


def downgrade() -> None:
    op.drop_table("cau_hinh")
    op.drop_table("log_api_vtp")
    op.drop_table("log_dong_bo_sheet")
    op.drop_index("ix_dia_danh_xa_ten_huyen", table_name="dia_danh_xa")
    op.drop_table("dia_danh_xa")
    op.drop_index("ix_dia_danh_huyen_ten_tinh", table_name="dia_danh_huyen")
    op.drop_table("dia_danh_huyen")
    op.drop_index("ix_dia_danh_tinh_ten", table_name="dia_danh_tinh")
    op.drop_table("dia_danh_tinh")
    op.drop_index("ix_hanh_trinh_pgh_phieu_giao_hang_id", table_name="hanh_trinh_pgh")
    op.drop_index("ix_hanh_trinh_pgh_ma_van_don_vtp", table_name="hanh_trinh_pgh")
    op.drop_table("hanh_trinh_pgh")
    op.drop_index("ix_phieu_giao_hang_du_lieu_sheet_id", table_name="phieu_giao_hang")
    op.drop_index("ix_phieu_giao_hang_ma_pgh_vtp", table_name="phieu_giao_hang")
    op.drop_index("ix_phieu_giao_hang_trang_thai", table_name="phieu_giao_hang")
    op.drop_table("phieu_giao_hang")
    op.drop_table("tai_khoan_vtp")
    op.drop_index("ix_du_lieu_sheet_ma_thung", table_name="du_lieu_sheet")
    op.drop_index("ix_du_lieu_sheet_ma_f_cha", table_name="du_lieu_sheet")
    op.drop_index("ix_du_lieu_sheet_ma_kien_k", table_name="du_lieu_sheet")
    op.drop_index("ix_du_lieu_sheet_ten_kh", table_name="du_lieu_sheet")
    op.drop_index("ix_du_lieu_sheet_ngay_chot", table_name="du_lieu_sheet")
    op.drop_index("ix_du_lieu_sheet_phuong_thuc_gui", table_name="du_lieu_sheet")
    op.drop_table("du_lieu_sheet")
