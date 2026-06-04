"""Client GATEWAY quanly.vanchuyenkinkin.com (hệ Tài chính) — tạo PGH kho đến + VTP
trong 1 call `add-update-delivery` (orderInformation.partner*), GIỐNG trang quản lý.

Auth: **cookie `access_token=<JWT>`** (KHÔNG phải Authorization Bearer). JWT lấy bằng
password grant identityapi — CÙNG token với khoden_client (iss=identityapi.vanchuyenkinkin.com,
client_id=Kinkin, aud gồm WarehouseExportService). Xem docs/quanly-pgh-api.md.

Gateway định tuyến theo prefix: KhoDen/..., CommonKDN/... (ASP.NET, case-insensitive).
"""
from __future__ import annotations

from typing import Any, Optional

import httpx

from app.core.config import settings
from app.integrations import khoden_client as kc


class QuanlyError(Exception):
    pass


def _cookies() -> dict[str, str]:
    # Token identityapi (lexuantruong) — gateway nhận qua cookie access_token
    return {"access_token": kc._lay_token()}


def _headers() -> dict[str, str]:
    return {"Content-Type": "application/json", "X-Requested-With": "XMLHttpRequest"}


def _get(path: str, params: Optional[dict] = None) -> Any:
    with httpx.Client(base_url=settings.KK_QUANLY_BASE, timeout=40.0) as c:
        r = c.get(path, params=params or {}, cookies=_cookies(),
                  headers={"X-Requested-With": "XMLHttpRequest"})
    if r.status_code != 200:
        raise QuanlyError(f"GET {path} {r.status_code}: {r.text[:400]}")
    return r.json()


def _post(path: str, body: dict) -> Any:
    with httpx.Client(base_url=settings.KK_QUANLY_BASE, timeout=40.0) as c:
        r = c.post(path, json=body, cookies=_cookies(), headers=_headers())
    if r.status_code != 200:
        raise QuanlyError(f"POST {path} {r.status_code}: {r.text[:500]}")
    return r.json()


def _as_list(d: Any) -> list[dict]:
    if isinstance(d, list):
        return d
    if isinstance(d, dict):
        return d.get("data") or d.get("items") or []
    return []


# ===== Tra khách (GIỐNG trang quản lý: gateway get-customer-code) =====

def tim_khach(term: str, is_parent: Optional[bool] = None) -> list[dict]:
    """POST KhoDen/DeliveryOrders/api/get-customer-code — typeahead khách GIỐNG trang quản lý.

    Trả list chuẩn hoá {id(GUID), code, name, phone, paymentType, isParent} để dùng chung
    với cache (kho_den_ref_doc). displayName của gateway → map sang name.
    """
    data = _post(
        "/KhoDen/DeliveryOrders/api/get-customer-code",
        {"customerCode": (term or "").strip(), "isParent": is_parent},
    )
    out: list[dict] = []
    for r in _as_list(data):
        out.append(
            {
                "id": r.get("id"),
                "code": r.get("code"),
                "name": r.get("displayName") or r.get("name"),
                "phone": r.get("phone"),
                "paymentType": r.get("paymentType"),
                "isParent": r.get("isParent"),
            }
        )
    return out


# ===== Đối tác VC + báo giá VTP =====

def ds_doi_tac() -> list[dict]:
    """GET get-list-delivery-partner → [{id, name}] (Viettel Post id = 1002)."""
    return _as_list(_get("/KhoDen/DeliveryOrders/api/get-list-delivery-partner"))


def bao_gia_vtp(body: dict) -> list[dict]:
    """POST get-list-service → danh sách dịch vụ VTP + giá cước.

    body: {PRODUCT_WEIGHT, PRODUCT_PRICE, MONEY_COLLECTION, PRODUCT_LENGTH/WIDTH/HEIGHT,
           KhoHangId, SENDER_PROVINCE/DISTRICT, RECEIVER_PROVINCE/DISTRICT}.
    Item: {mA_DV_CHINH, teN_DICHVU, thoI_GIAN, giA_CUOC}.
    """
    return _as_list(_post("/KhoDen/deliveryOrders/api/get-list-service", body))


# ===== Tạo PGH (kho đến + VTP) — 1 call =====

def tao_pgh(body: dict) -> dict:
    """POST add-update-delivery qua gateway → tạo PGH kho đến (+ VTP nếu body có partner*)."""
    resp = _post("/KhoDen/deliveryorders/api/add-update-delivery", body)
    return resp if isinstance(resp, dict) else {"data": resp, "responseStatus": True}


# ===== Địa chỉ nhận (DOReceiveAddress) — dùng khi tạo địa chỉ mới qua gateway =====

def ds_dia_chi_khach(customer_id: str) -> list[dict]:
    """POST DOReceiveAddress/get-data {customerId} → list địa chỉ của khách."""
    return _as_list(_post("/KhoDen/deliveryorders/api/DOReceiveAddress/get-data",
                          {"customerId": customer_id}))


def tao_dia_chi(body: dict) -> dict:
    """POST DOReceiveAddress/save-data → tạo/sửa địa chỉ nhận."""
    resp = _post("/KhoDen/deliveryorders/api/DOReceiveAddress/save-data", body)
    return resp if isinstance(resp, dict) else {"data": resp}


# ===== Kho =====

def ds_kho() -> list[dict]:
    """GET CommonKDN/KKWarehouses/api/list → danh sách kho."""
    return _as_list(_get("/CommonKDN/KKWarehouses/api/list"))
