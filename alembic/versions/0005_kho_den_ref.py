"""kho_den_ref — cache reference data hệ kho đến (kd_*)

Revision ID: 0005_kho_den_ref
Revises: 0004_pgh_kinkin
Create Date: 2026-06-04

Tạo các bảng cache: khách, địa chỉ giao, địa danh (nation/tinh/huyen/xa),
kiện F/K, kho, và log sync.
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "0005_kho_den_ref"
down_revision: Union[str, None] = "0004_pgh_kinkin"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _common_origin():
    return [
        sa.Column("host_origin", sa.Text(), nullable=False, server_default="that"),
        sa.Column("tao_luc", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    ]


def upgrade() -> None:
    op.create_table(
        "kd_khach_hang",
        sa.Column("customer_id", sa.Text(), primary_key=True),
        sa.Column("kinkin_id", sa.BigInteger()),
        sa.Column("code", sa.Text()),
        sa.Column("name", sa.Text()),
        sa.Column("phone", sa.Text()),
        sa.Column("address", sa.Text()),
        sa.Column("payment_type", sa.Integer()),
        sa.Column("group_name", sa.Text()),
        sa.Column("parent_id", sa.Text()),
        sa.Column("is_parent", sa.Boolean()),
        sa.Column("payload_raw", postgresql.JSONB()),
        sa.Column("host_origin", sa.Text(), nullable=False, server_default="that"),
        sa.Column("last_sync_luc", sa.DateTime(timezone=True)),
        sa.Column("tao_luc", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("sua_luc", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_kd_khach_hang_code", "kd_khach_hang", ["code"])
    op.create_index("ix_kd_khach_hang_host", "kd_khach_hang", ["host_origin"])

    op.create_table(
        "kd_dia_chi_giao",
        sa.Column("address_id", sa.Text(), primary_key=True),
        sa.Column("type_id", sa.Integer()),
        sa.Column("customer_id", sa.Text()),
        sa.Column("customer_code", sa.Text()),
        sa.Column("receiver", sa.Text()),
        sa.Column("phone", sa.Text()),
        sa.Column("nation_id", sa.Text()),
        sa.Column("nation_name", sa.Text()),
        sa.Column("province_id", sa.Text()),
        sa.Column("province_name", sa.Text()),
        sa.Column("district_id", sa.Text()),
        sa.Column("district_name", sa.Text()),
        sa.Column("ward_id", sa.Text()),
        sa.Column("ward_name", sa.Text()),
        sa.Column("address", sa.Text()),
        sa.Column("delivery_point_code", sa.Text()),
        sa.Column("is_active", sa.Boolean()),
        sa.Column("payload_raw", postgresql.JSONB()),
        sa.Column("host_origin", sa.Text(), nullable=False, server_default="that"),
        sa.Column("last_sync_luc", sa.DateTime(timezone=True)),
        sa.Column("tao_luc", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("sua_luc", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_kd_dia_chi_giao_customer_id", "kd_dia_chi_giao", ["customer_id"])
    op.create_index("ix_kd_dia_chi_giao_customer_code", "kd_dia_chi_giao", ["customer_code"])

    op.create_table(
        "kd_nation",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("name", sa.Text()),
        *_common_origin(),
    )

    op.create_table(
        "kd_tinh",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("nation_id", sa.Text()),
        sa.Column("name", sa.Text()),
        sa.Column("code", sa.Text()),
        sa.Column("name_norm", sa.Text()),
        *_common_origin(),
    )
    op.create_index("ix_kd_tinh_norm", "kd_tinh", ["name_norm"])
    op.create_index("ix_kd_tinh_nation", "kd_tinh", ["nation_id"])

    op.create_table(
        "kd_huyen",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("province_id", sa.Text()),
        sa.Column("name", sa.Text()),
        sa.Column("code", sa.Text()),
        sa.Column("name_norm", sa.Text()),
        *_common_origin(),
    )
    op.create_index("ix_kd_huyen_province", "kd_huyen", ["province_id"])
    op.create_index("ix_kd_huyen_norm", "kd_huyen", ["name_norm"])

    op.create_table(
        "kd_xa",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("district_id", sa.Text()),
        sa.Column("name", sa.Text()),
        sa.Column("code", sa.Text()),
        sa.Column("name_norm", sa.Text()),
        *_common_origin(),
    )
    op.create_index("ix_kd_xa_district", "kd_xa", ["district_id"])
    op.create_index("ix_kd_xa_norm", "kd_xa", ["name_norm"])

    op.create_table(
        "kd_kien_f",
        sa.Column("package_f_id", sa.Text(), primary_key=True),
        sa.Column("package_f_code", sa.Text()),
        sa.Column("package_f_name", sa.Text()),
        sa.Column("customer_code", sa.Text()),
        sa.Column("warehouse_id", sa.Text()),
        sa.Column("current_status", sa.Integer()),
        sa.Column("status_name", sa.Text()),
        sa.Column("weight", sa.Numeric(12, 3)),
        sa.Column("mawb", sa.Text()),
        sa.Column("code_tracking", sa.Text()),
        sa.Column("payload_raw", postgresql.JSONB()),
        sa.Column("host_origin", sa.Text(), nullable=False, server_default="that"),
        sa.Column("last_sync_luc", sa.DateTime(timezone=True)),
        sa.Column("tao_luc", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("sua_luc", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_kd_kien_f_code", "kd_kien_f", ["package_f_code"])
    op.create_index("ix_kd_kien_f_name", "kd_kien_f", ["package_f_name"])
    op.create_index("ix_kd_kien_f_customer", "kd_kien_f", ["customer_code"])

    op.create_table(
        "kd_kien_k",
        sa.Column("package_k_id", sa.Text(), primary_key=True),
        sa.Column("package_k_code", sa.Text()),
        sa.Column("package_k_name", sa.Text()),
        sa.Column("customer_code", sa.Text()),
        sa.Column("warehouse_id", sa.Text()),
        sa.Column("current_status", sa.Integer()),
        sa.Column("status_name", sa.Text()),
        sa.Column("weight", sa.Numeric(12, 3)),
        sa.Column("payload_raw", postgresql.JSONB()),
        sa.Column("host_origin", sa.Text(), nullable=False, server_default="that"),
        sa.Column("last_sync_luc", sa.DateTime(timezone=True)),
        sa.Column("tao_luc", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("sua_luc", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_kd_kien_k_code", "kd_kien_k", ["package_k_code"])
    op.create_index("ix_kd_kien_k_customer", "kd_kien_k", ["customer_code"])

    op.create_table(
        "kd_kho",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("kinkin_id", sa.BigInteger()),
        sa.Column("name", sa.Text()),
        sa.Column("code", sa.Text()),
        *_common_origin(),
    )

    op.create_table(
        "kd_sync_log",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("bang", sa.Text(), nullable=False),
        sa.Column("endpoint", sa.Text()),
        sa.Column("host_origin", sa.Text()),
        sa.Column("bat_dau_luc", sa.DateTime(timezone=True)),
        sa.Column("ket_thuc_luc", sa.DateTime(timezone=True)),
        sa.Column("so_doc", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("them_moi", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cap_nhat", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("so_loi", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("trang_thai", sa.Text()),
        sa.Column("chi_tiet_loi", sa.Text()),
        sa.Column("tao_luc", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_kd_sync_log_bang", "kd_sync_log", ["bang"])


def downgrade() -> None:
    for tbl in (
        "kd_sync_log", "kd_kho", "kd_kien_k", "kd_kien_f",
        "kd_xa", "kd_huyen", "kd_tinh", "kd_nation",
        "kd_dia_chi_giao", "kd_khach_hang",
    ):
        op.drop_table(tbl)
