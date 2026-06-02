"""pgh_kinkin_columns

Revision ID: 0004_pgh_kinkin
Revises: 0003_cache_kinkin
Create Date: 2026-06-02

Thêm 8 cột vào phieu_giao_hang để:
  - Lưu PGH song song trên Kinkin warehouse (ma_pgh_kinkin, kho_den_id, trang_thai_kinkin,
    kinkin_request_json, kinkin_response_json, kinkin_loi_message, kinkin_tao_luc)
  - Lưu trường thiếu khi data sheet chưa đủ (thieu_truong_json)
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "0004_pgh_kinkin"
down_revision: Union[str, None] = "0003_cache_kinkin"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("phieu_giao_hang", sa.Column("ma_pgh_kinkin", sa.Text()))
    op.add_column("phieu_giao_hang", sa.Column("kho_den_id", sa.Text()))
    op.add_column(
        "phieu_giao_hang",
        sa.Column(
            "trang_thai_kinkin",
            sa.Text(),
            nullable=False,
            server_default="chua_tao",
        ),
    )
    op.add_column("phieu_giao_hang", sa.Column("kinkin_request_json", postgresql.JSONB()))
    op.add_column("phieu_giao_hang", sa.Column("kinkin_response_json", postgresql.JSONB()))
    op.add_column("phieu_giao_hang", sa.Column("kinkin_loi_message", sa.Text()))
    op.add_column(
        "phieu_giao_hang", sa.Column("kinkin_tao_luc", sa.DateTime(timezone=True))
    )
    op.add_column("phieu_giao_hang", sa.Column("thieu_truong_json", postgresql.JSONB()))

    op.create_unique_constraint(
        "uq_phieu_giao_hang_ma_pgh_kinkin", "phieu_giao_hang", ["ma_pgh_kinkin"]
    )
    op.create_index(
        "ix_phieu_giao_hang_trang_thai_kinkin",
        "phieu_giao_hang",
        ["trang_thai_kinkin"],
    )


def downgrade() -> None:
    op.drop_index("ix_phieu_giao_hang_trang_thai_kinkin", table_name="phieu_giao_hang")
    op.drop_constraint(
        "uq_phieu_giao_hang_ma_pgh_kinkin", "phieu_giao_hang", type_="unique"
    )
    op.drop_column("phieu_giao_hang", "thieu_truong_json")
    op.drop_column("phieu_giao_hang", "kinkin_tao_luc")
    op.drop_column("phieu_giao_hang", "kinkin_loi_message")
    op.drop_column("phieu_giao_hang", "kinkin_response_json")
    op.drop_column("phieu_giao_hang", "kinkin_request_json")
    op.drop_column("phieu_giao_hang", "trang_thai_kinkin")
    op.drop_column("phieu_giao_hang", "kho_den_id")
    op.drop_column("phieu_giao_hang", "ma_pgh_kinkin")
