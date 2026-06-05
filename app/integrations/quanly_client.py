"""Client GATEWAY quanly.vanchuyenkinkin.com (hệ Tài chính) — tạo PGH kho đến + VTP
trong 1 call `add-update-delivery` (orderInformation.partner*), GIỐNG trang quản lý.

Auth: **cookie `access_token=<JWT>`** (KHÔNG phải Authorization Bearer). JWT lấy bằng
password grant identityapi — CÙNG token với khoden_client (iss=identityapi.vanchuyenkinkin.com,
client_id=Kinkin, aud gồm WarehouseExportService). Xem docs/quanly-pgh-api.md.

Gateway định tuyến theo prefix: KhoDen/..., CommonKDN/... (ASP.NET, case-insensitive).
"""
from __future__ import annotations

import time
from typing import Any, Optional

import httpx

from app.core.config import settings
from app.integrations import khoden_client as kc


class QuanlyError(Exception):
    pass


# Client HTTP dùng chung (keep-alive theo host) — tránh bắt tay TLS mỗi call.
_HTTP = httpx.Client(
    base_url=settings.KK_QUANLY_BASE,
    timeout=httpx.Timeout(40.0, connect=8.0),
    limits=httpx.Limits(max_keepalive_connections=20, max_connections=40, keepalive_expiry=60.0),
)


def _cookies() -> dict[str, str]:
    # Token identityapi (lexuantruong) — gateway nhận qua cookie access_token
    return {"access_token": kc._lay_token()}


def _headers() -> dict[str, str]:
    return {"Content-Type": "application/json", "X-Requested-With": "XMLHttpRequest"}


def _get(path: str, params: Optional[dict] = None) -> Any:
    r = _HTTP.get(path, params=params or {}, cookies=_cookies(),
                  headers={"X-Requested-With": "XMLHttpRequest"})
    if r.status_code != 200:
        raise QuanlyError(f"GET {path} {r.status_code}: {r.text[:400]}")
    return r.json()


def _post(path: str, body: dict) -> Any:
    r = _HTTP.post(path, json=body, cookies=_cookies(), headers=_headers())
    if r.status_code != 200:
        raise QuanlyError(f"POST {path} {r.status_code}: {r.text[:500]}")
    return r.json()


def _as_list(d: Any) -> list[dict]:
    if isinstance(d, list):
        return d
    if isinstance(d, dict):
        return d.get("data") or d.get("items") or []
    return []


# ===== Tra khách (GIỐNG trang Danh sách khách hàng: list-server-side-parent) =====

# Cột DataTables của trang danh sách khách hàng (server cần để biết cột searchable).
_CUST_COLS = [
    {"data": d, "name": "", "searchable": True, "orderable": False, "search": {"value": "", "regex": False}}
    for d in [
        "isHaveChild", "id", "code", "name", "userManager", "nhomBangGiaSanStr",
        "isNotActive", "isApprovedStatus", "createDate", "updateDate", "id",
    ]
]


def tim_khach_list(term: str, length: int = 20) -> list[dict]:
    """POST customer/api/list-server-side-parent (searchAll=term) — tra khách GIỐNG trang
    Danh sách khách hàng. `name` = TÊN THẬT, `displayName` = mã. searchAll khớp mã + tên
    (KHÔNG khớp sđt); không có → rỗng (dùng để báo "chưa có → tạo tài khoản").

    LƯU Ý: `id` ở đây là INT (kinkinId) — KHÔNG phải GUID. Tạo PGH cần GUID → resolve
    code→GUID qua core (kc.lay_customer_id) ở bước chọn khách.
    """
    term = (term or "").strip()
    if not term:
        return []
    body = {
        "draw": 1, "columns": _CUST_COLS, "order": [], "start": 0, "length": length,
        "search": {"value": "", "regex": False}, "searchAll": term,
        "nguoiQuanLy": None, "trangThaiHoatDong": "", "bangGiaSanId": 0,
    }
    data = _post("/customer/api/list-server-side-parent", body)
    rows = data.get("data") if isinstance(data, dict) else (data or [])
    out: list[dict] = []
    for r in rows or []:
        out.append(
            {
                "id": r.get("id"),  # INT kinkinId, KHÔNG phải GUID
                "code": r.get("code"),
                "name": r.get("name"),
                "displayName": r.get("displayName"),
                "phone": r.get("phone"),
                "paymentType": r.get("paymentType"),
                "groupName": r.get("groupName"),
                "address": r.get("address"),
            }
        )
    return out


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
                "id": r.get("id"),  # GUID — orderable, dùng tạo PGH luôn
                "code": r.get("code"),
                "name": r.get("name") or r.get("displayName"),
                "phone": r.get("phone"),
                "paymentType": r.get("paymentType"),
                "groupName": r.get("groupName"),
                "isParent": r.get("isParent"),
            }
        )
    return out


# ===== Đối tác VC + báo giá VTP =====

_doi_tac_cache: dict = {"value": None, "at": 0.0}
_DOI_TAC_TTL = 1800.0  # 30 phút — DS đối tác gần như tĩnh, tránh gọi gateway mỗi lần mở form


def ds_doi_tac() -> list[dict]:
    """GET get-list-delivery-partner → [{id, name}] (Viettel Post id = 1002). Cache 30'."""
    now = time.monotonic()
    c = _doi_tac_cache
    if c["value"] is not None and (now - c["at"]) < _DOI_TAC_TTL:
        return c["value"]
    data = _as_list(_get("/KhoDen/DeliveryOrders/api/get-list-delivery-partner"))
    if data:
        c["value"] = data
        c["at"] = now
    return data


def format_address(text: str) -> dict:
    """GET formatAddress?input= → tách địa chỉ tự do thành tỉnh/huyện + **ID KinKin số**.

    Trả (đã xác minh hệ thật): {provincesId(GUID), districtId(GUID), provincesName,
    districtName, provinceKinKinId(số), districtKinKinId(số), address}. provinceKinKinId/
    districtKinKinId chính là field SENDER_*/RECEIVER_* mà get-list-service cần.
    """
    if not (text or "").strip():
        return {}
    r = _get("/KhoDen/deliveryorders/api/formatAddress", {"input": text})
    return r if isinstance(r, dict) else {}


def bao_gia_vtp(body: dict) -> list[dict]:
    """POST get-list-service → danh sách dịch vụ VTP + giá cước.

    body: {PRODUCT_WEIGHT, PRODUCT_PRICE, MONEY_COLLECTION, PRODUCT_LENGTH/WIDTH/HEIGHT,
           KhoHangId, SENDER_PROVINCE/DISTRICT, RECEIVER_PROVINCE/DISTRICT}.
    SENDER_*/RECEIVER_* = provinceKinKinId/districtKinKinId (SỐ) từ format_address — KHÔNG phải
    GUID/tên (truyền GUID → backend 400 'Object reference not set'). Item trả về:
    {mA_DV_CHINH (mã DV), teN_DICHVU (tên), thoI_GIAN (thời gian), giA_CUOC (giá cước)}.
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
