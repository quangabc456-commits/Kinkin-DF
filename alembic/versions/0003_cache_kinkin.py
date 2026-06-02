"""cache_kinkin_ma

Revision ID: 0003_cache_kinkin
Revises: 0002_tai_khoan_kinkin
Create Date: 2026-06-02

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "0003_cache_kinkin"
down_revision: Union[str, None] = "0002_tai_khoan_kinkin"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "cache_kinkin_ma",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("code", sa.Text(), nullable=False, unique=True),
        sa.Column("loai", sa.Text()),
        sa.Column("ma_don_chinh", sa.Text()),
        sa.Column("bill_code", sa.Text()),
        sa.Column("trang_thai", sa.Text()),
        sa.Column("ten_kho", sa.Text()),
        sa.Column("warehouse_id", sa.Text()),
        sa.Column("ma_kien_k", sa.Text()),
        sa.Column("ma_f_cha", sa.Text()),
        sa.Column("ma_thung", sa.Text()),
        sa.Column("nguoi_nhan", sa.Text()),
        sa.Column("sdt_nguoi_nhan", sa.Text()),
        sa.Column("dia_chi_nhan", sa.Text()),
        sa.Column("nha_van_chuyen", sa.Text()),
        sa.Column("so_luong", sa.BigInteger()),
        sa.Column("tong_tien_vnd", sa.BigInteger()),
        sa.Column("ngay_tao_kinkin", sa.DateTime(timezone=True)),
        sa.Column("ngay_cap_nhat_kinkin", sa.DateTime(timezone=True)),
        sa.Column("payload_raw", postgresql.JSONB()),
        sa.Column("last_sync_luc", sa.DateTime(timezone=True)),
        sa.Column("last_sync_loi", sa.Text()),
        sa.Column("tao_luc", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("sua_luc", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_cache_kinkin_ma_loai", "cache_kinkin_ma", ["loai"])
    op.create_index("ix_cache_kinkin_ma_last_sync", "cache_kinkin_ma", ["last_sync_luc"])
    op.create_index("ix_cache_kinkin_ma_bill_code", "cache_kinkin_ma", ["bill_code"])


def downgrade() -> None:
    op.drop_index("ix_cache_kinkin_ma_bill_code", table_name="cache_kinkin_ma")
    op.drop_index("ix_cache_kinkin_ma_last_sync", table_name="cache_kinkin_ma")
    op.drop_index("ix_cache_kinkin_ma_loai", table_name="cache_kinkin_ma")
    op.drop_table("cache_kinkin_ma")
