"""phieu_giao_hang: tai_khoan_vtp_id nullable (cho PGH kho-đến-only)

Revision ID: 0006_pgh_vtp_nullable
Revises: 0005_kho_den_ref
Create Date: 2026-06-04

Luồng hợp nhất: 1 row phieu_giao_hang có thể là kho-đến-only (chưa/không dùng VTP)
→ không bắt buộc gắn tài khoản VTP.
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op


revision: str = "0006_pgh_vtp_nullable"
down_revision: Union[str, None] = "0005_kho_den_ref"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("phieu_giao_hang", "tai_khoan_vtp_id", nullable=True)


def downgrade() -> None:
    op.alter_column("phieu_giao_hang", "tai_khoan_vtp_id", nullable=False)
