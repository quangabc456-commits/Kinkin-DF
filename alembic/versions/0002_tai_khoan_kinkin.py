"""tai_khoan_kinkin

Revision ID: 0002_tai_khoan_kinkin
Revises: 0001_initial
Create Date: 2026-06-01

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "0002_tai_khoan_kinkin"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tai_khoan_kinkin",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("ten_hien_thi", sa.Text(), nullable=False),
        sa.Column("username", sa.Text(), nullable=False, unique=True),
        sa.Column("password_enc", sa.Text()),
        sa.Column("warehouse_id", sa.Text()),
        sa.Column("customer_code", sa.Text()),
        sa.Column("package_k_apikey", sa.Text()),
        sa.Column("token_hien_tai", sa.Text()),
        sa.Column("token_het_han_luc", sa.DateTime(timezone=True)),
        sa.Column(
            "base_identity",
            sa.Text(),
            server_default="https://identityapi.vanchuyenkinkin.com",
        ),
        sa.Column(
            "base_export",
            sa.Text(),
            server_default="https://warehouseexportapi.vanchuyenkinkin.com",
        ),
        sa.Column(
            "base_departure",
            sa.Text(),
            server_default="https://warehousedepartureapi.vanchuyenkinkin.com",
        ),
        sa.Column("mac_dinh", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("kich_hoat", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("tao_luc", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("sua_luc", sa.DateTime(timezone=True)),
    )


def downgrade() -> None:
    op.drop_table("tai_khoan_kinkin")
