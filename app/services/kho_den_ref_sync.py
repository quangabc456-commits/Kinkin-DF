"""Hút reference data hệ KHO ĐẾN về DB (bảng kd_*) cho màn hình tạo PGH.

Chạy bằng CLI `python -m app.cli.sync_kho_den` hoặc gọi `sync_all(session)`.
Cần token kho đến hợp lệ (KK_KHODEN_USERNAME/PASSWORD hệ thật). Upsert idempotent
(on_conflict_do_update theo PK GUID). Ghi nhật ký vào kd_sync_log.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Callable, Optional

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.integrations import khoden_client as kc
from app.models import (
    KdDiaChiGiao,
    KdHuyen,
    KdKho,
    KdKhachHang,
    KdKienF,
    KdNation,
    KdSyncLog,
    KdTinh,
    KdXa,
)

HOST = "that"  # môi trường hiện tại (hosts trỏ vanchuyenkinkin.com)
_CHUNK = 500


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _num(v: Any) -> Optional[Decimal]:
    if v in (None, ""):
        return None
    try:
        return Decimal(str(v))
    except (InvalidOperation, ValueError, TypeError):
        return None


def _upsert(session: Session, model: Any, rows: list[dict], pk: str) -> int:
    """Bulk upsert (chunk 500) theo PK. tao_luc giữ nguyên khi update."""
    if not rows:
        return 0
    cols = {c.name for c in model.__table__.columns}
    total = 0
    for i in range(0, len(rows), _CHUNK):
        chunk = rows[i : i + _CHUNK]
        stmt = pg_insert(model).values(chunk)
        set_ = {
            k: getattr(stmt.excluded, k)
            for k in chunk[0].keys()
            if k in cols and k not in (pk, "tao_luc")
        }
        if "sua_luc" in cols:
            set_["sua_luc"] = func.now()  # onupdate ORM không fire trên Core upsert
        stmt = stmt.on_conflict_do_update(index_elements=[pk], set_=set_)
        session.execute(stmt)
        total += len(chunk)
    return total


def _run(session: Session, bang: str, endpoint: str, fn: Callable[[], int]) -> dict:
    """Chạy 1 bước sync trong SAVEPOINT riêng + commit độc lập; KHÔNG raise (thu lỗi vào log).

    Một bước lỗi chỉ rollback chính nó (begin_nested), không poison transaction → các bước
    khác + log vẫn bền vững.
    """
    log = KdSyncLog(bang=bang, endpoint=endpoint, host_origin=HOST, bat_dau_luc=_now())
    try:
        with session.begin_nested():  # SAVEPOINT: lỗi chỉ rollback bước này
            n = fn()
        log.so_doc = n
        log.trang_thai = "ok"
        result = {"bang": bang, "so_doc": n, "ok": True}
    except Exception as e:  # noqa: BLE001 — log mọi lỗi sync, tiếp bước khác
        log.trang_thai = "loi"
        log.so_loi = 1
        log.chi_tiet_loi = str(e)[:1000]
        result = {"bang": bang, "ok": False, "loi": str(e)[:300]}
    log.ket_thuc_luc = _now()
    try:
        session.add(log)
        session.commit()  # commit độc lập từng bước → log + data sống dù bước sau lỗi
    except Exception:
        session.rollback()
    return result


# ===== Từng bảng =====

def sync_quoc_gia(session: Session) -> int:
    rows = [
        {"id": it["id"], "name": it.get("name"), "host_origin": HOST}
        for it in kc.ds_quoc_gia()
        if it.get("id")
    ]
    return _upsert(session, KdNation, rows, "id")


def sync_tinh(session: Session, naction_id: str = kc.NATION_VIETNAM_ID) -> int:
    rows = [
        {
            "id": it["id"], "nation_id": naction_id, "name": it.get("name"),
            "code": it.get("code"), "name_norm": kc.chuan_hoa(it.get("name")), "host_origin": HOST,
        }
        for it in kc.ds_tinh(naction_id)
        if it.get("id")
    ]
    return _upsert(session, KdTinh, rows, "id")


def sync_dia_danh_deep(session: Session, naction_id: str = kc.NATION_VIETNAM_ID) -> int:
    """Kéo đủ Tỉnh→Huyện→Xã (nặng). Trả tổng số bản ghi xã."""
    n_xa = 0
    for tinh in kc.ds_tinh(naction_id):
        if not tinh.get("id"):
            continue
        huyen_rows = [
            {
                "id": h["id"], "province_id": tinh["id"], "name": h.get("name"),
                "code": h.get("code"), "name_norm": kc.chuan_hoa(h.get("name")), "host_origin": HOST,
            }
            for h in kc.ds_huyen(tinh["id"])
            if h.get("id")
        ]
        _upsert(session, KdHuyen, huyen_rows, "id")
        for h in huyen_rows:
            xa_rows = [
                {
                    "id": x["id"], "district_id": h["id"], "name": x.get("name"),
                    "code": x.get("code"), "name_norm": kc.chuan_hoa(x.get("name")), "host_origin": HOST,
                }
                for x in kc.ds_xa(h["id"])
                if x.get("id")
            ]
            n_xa += _upsert(session, KdXa, xa_rows, "id")
    return n_xa


def sync_kho(session: Session) -> int:
    rows = [
        {
            "id": str(it.get("id")), "kinkin_id": it.get("kinkinId"),
            "name": it.get("name"), "code": it.get("code"), "host_origin": HOST,
        }
        for it in kc.ds_kho()
        if it.get("id") is not None
    ]
    return _upsert(session, KdKho, rows, "id")


def sync_dia_chi_giao(session: Session, page_size: int = 500) -> int:
    rows: list[dict] = []
    page = 1
    while True:
        kq = kc.ds_dia_chi(page=page, page_size=page_size)
        data = kq.get("data") or []
        for d in data:
            if not d.get("id"):
                continue
            rows.append({
                "address_id": d["id"], "type_id": d.get("typeId"),
                "customer_id": d.get("customerId"), "customer_code": d.get("customerCode"),
                "receiver": d.get("receiver"), "phone": d.get("phone"),
                "nation_id": d.get("nationId"), "nation_name": d.get("nationName"),
                "province_id": d.get("provinceId"), "province_name": d.get("provinceName"),
                "district_id": d.get("districtId"), "district_name": d.get("districtName"),
                "ward_id": d.get("wardId"), "ward_name": d.get("wardName"),
                "address": d.get("address"), "delivery_point_code": d.get("deliveryPointCode"),
                "is_active": d.get("isActive"), "payload_raw": d,
                "host_origin": HOST, "last_sync_luc": _now(),
            })
        total = kq.get("total") or 0
        if not data or page * page_size >= total:
            break
        page += 1
    return _upsert(session, KdDiaChiGiao, rows, "address_id")


def sync_khach(session: Session, page_size: int = 500) -> int:
    """Bulk khách (best-effort — envelope customer/get-list cần xác minh hệ thật)."""
    rows: list[dict] = []
    page = 1
    while True:
        kq = kc.ds_khach_all(page=page, page_size=page_size)
        data = kq.get("data") if isinstance(kq, dict) else kq
        if isinstance(data, dict):
            data = data.get("items") or data.get("data") or []
        data = data or []
        for it in data:
            if not it.get("id"):
                continue
            rows.append({
                "customer_id": it["id"], "kinkin_id": it.get("kinkinId"),
                "code": it.get("code"), "name": it.get("name"), "phone": it.get("phone"),
                "address": it.get("address"), "payment_type": it.get("paymentType"),
                "group_name": it.get("groupName"), "parent_id": it.get("parentId"),
                "is_parent": it.get("isParent"), "payload_raw": it,
                "host_origin": HOST, "last_sync_luc": _now(),
            })
        total = (kq.get("total") if isinstance(kq, dict) else 0) or 0
        if not data or page * page_size >= total:
            break
        page += 1
    return _upsert(session, KdKhachHang, rows, "customer_id")


def sync_kien_f(session: Session, customer_code: str) -> int:
    rows = []
    for f in kc.ds_kien_f(customer_code):
        if not f.get("packageFId"):
            continue
        rows.append({
            "package_f_id": f["packageFId"], "package_f_code": f.get("packageFCode"),
            "package_f_name": f.get("packageFName"), "customer_code": f.get("customerCode") or customer_code,
            "warehouse_id": str(f.get("wareHouseId")) if f.get("wareHouseId") is not None else None,
            "current_status": f.get("currentPackageFStatus"), "status_name": f.get("packageFStatusName"),
            "weight": _num(f.get("packageFWeight")), "mawb": f.get("mawb"),
            "code_tracking": f.get("codeTracking") or f.get("packageFCode"),
            "payload_raw": f, "host_origin": HOST, "last_sync_luc": _now(),
        })
    return _upsert(session, KdKienF, rows, "package_f_id")


# ===== Tổng hợp =====

def sync_all(session: Session, deep_dia_danh: bool = False) -> list[dict]:
    """Sync các bảng ít/bán biến đổi. Kiện F sync on-demand theo khách (gọi sync_kien_f riêng)."""
    out = [
        _run(session, "kd_nation", "nactions/get-all", lambda: sync_quoc_gia(session)),
        _run(session, "kd_tinh", "Provinces/get-by-condition", lambda: sync_tinh(session)),
        _run(session, "kd_kho", "warehouse/get-list", lambda: sync_kho(session)),
        _run(session, "kd_dia_chi_giao", "deliveryAddress/get-list", lambda: sync_dia_chi_giao(session)),
        _run(session, "kd_khach_hang", "customer/get-list", lambda: sync_khach(session)),
    ]
    if deep_dia_danh:
        out.append(_run(session, "kd_xa", "Wards/get-by-conditon", lambda: sync_dia_danh_deep(session)))
    session.commit()
    return out
