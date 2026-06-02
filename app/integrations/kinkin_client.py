from __future__ import annotations

import threading
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import httpx

from app.core.config import settings


SCOPE = "Identity KinkinCore KinkinReport offline_access WarehouseDeparture WarehouseExport"
CLIENT_ID = "Kinkin"
CLIENT_SECRET = "KinkinAPP"


class KinkinError(Exception):
    pass


_token_lock = threading.Lock()
_token_cache: dict[str, Any] = {"value": None, "expires_at": None}


def _co_cau_hinh() -> None:
    if not settings.KK_USERNAME or not settings.KK_PASSWORD:
        raise KinkinError(
            "Thiếu KK_USERNAME / KK_PASSWORD trong .env. Bổ sung rồi restart app."
        )


def _lay_token(force_refresh: bool = False) -> str:
    """Lấy token, cache trong memory ~50 phút (token thật ~1h)."""
    _co_cau_hinh()

    with _token_lock:
        if not force_refresh:
            val = _token_cache["value"]
            exp = _token_cache["expires_at"]
            if val and exp and exp > datetime.now(timezone.utc) + timedelta(minutes=5):
                return val

        body = {
            "grant_type": "password",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "scope": SCOPE,
            "username": settings.KK_USERNAME,
            "password": settings.KK_PASSWORD,
        }
        with httpx.Client(base_url=settings.KK_BASE_IDENTITY, timeout=30.0) as c:
            r = c.post(
                "/connect/token",
                data=body,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        if r.status_code != 200:
            raise KinkinError(f"connect/token {r.status_code}: {r.text[:300]}")
        data = r.json()
        token = data.get("access_token")
        expires_in = data.get("expires_in") or 3600
        if not token:
            raise KinkinError(f"connect/token không trả access_token: {data}")
        _token_cache["value"] = token
        _token_cache["expires_at"] = datetime.now(timezone.utc) + timedelta(seconds=int(expires_in))
        return token


def trang_thai_token() -> dict[str, Any]:
    """Trả trạng thái token để hiển thị trên UI cài đặt."""
    val = _token_cache["value"]
    exp = _token_cache["expires_at"]
    return {
        "co_token": bool(val),
        "het_han_luc": exp.isoformat() if exp else None,
    }


def _headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {_lay_token()}", "Content-Type": "application/json"}


def _post(base: str, path: str, body: dict, *, custom_headers: Optional[dict] = None) -> dict:
    h = custom_headers if custom_headers is not None else _headers()
    with httpx.Client(base_url=base, timeout=30.0) as c:
        r = c.post(path, json=body, headers=h)
    if r.status_code != 200:
        raise KinkinError(f"POST {path} {r.status_code}: {r.text[:300]}")
    return r.json()


def _get(base: str, path: str, params: dict, *, custom_headers: Optional[dict] = None) -> dict:
    h = custom_headers if custom_headers is not None else _headers()
    with httpx.Client(base_url=base, timeout=30.0) as c:
        r = c.get(path, params=params, headers=h)
    if r.status_code != 200:
        raise KinkinError(f"GET {path} {r.status_code}: {r.text[:300]}")
    return r.json()


# ===== E.2 PGH =====

def pgh_list(
    search_content: str = "",
    warehouse_id: str = "",
    customer_code: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    body = {
        "searchContent": search_content,
        "warehouseId": warehouse_id,
        "customerCode": customer_code if customer_code is not None else settings.KK_CUSTOMER_CODE,
        "fromDate": from_date,
        "toDate": to_date,
        "page": page,
        "pageSize": page_size,
    }
    return _post(settings.KK_BASE_WAREHOUSE, "/warehouseexport/api/deliveryorders/get-list", body)


def pgh_detail_by_code(code: str) -> dict:
    return _get(
        settings.KK_BASE_WAREHOUSE,
        "/warehouseexport/api/deliveryorders/get-Delivery-By-Code",
        {"code": code},
    )


def pgh_see_delivery_note(delivery_code: str, warehouse_id: str = "") -> dict:
    body = {"deliveryCode": delivery_code, "isSee": True, "warehouseId": warehouse_id}
    return _post(
        settings.KK_BASE_WAREHOUSE,
        "/warehouseexport/api/deliveryorders/get-see-delivery-note",
        body,
    )


# ===== E.3 F =====

def f_list(package_f_name: str, warehouse_id: str = "", page: int = 1, page_size: int = 20) -> dict:
    body = {
        "warehouseId": warehouse_id,
        "packageFName": package_f_name,
        "page": page,
        "pageSize": page_size,
    }
    return _post(
        settings.KK_BASE_WAREHOUSE, "/warehouseexport/api/packageF/common/get-list-paginate", body
    )


# ===== E.4 VK =====

def vk_list(code: str, page: int = 1, page_size: int = 20) -> dict:
    body = {"code": code, "page": page, "pageSize": page_size}
    return _post(
        settings.KK_BASE_WAREHOUSE,
        "/warehouseexport/api/packageVK/common/get-list-paginate",
        body,
    )


def vk_detail(package_vk_id: str) -> dict:
    body = {"packageVkId": package_vk_id}
    return _post(
        settings.KK_BASE_WAREHOUSE,
        "/warehouseexport/api/packageVK/common/get-package-detail",
        body,
    )


# ===== E.5 K =====

def k_list(
    code: str,
    warehouse_id: str = "",
    month: Optional[int] = None,
    year: Optional[int] = None,
    date: Optional[str] = None,
) -> dict:
    body: dict[str, Any] = {"wWareHouseId": warehouse_id, "code": code}
    if month is not None:
        body["month"] = month
    if year is not None:
        body["year"] = year
    if date is not None:
        body["date"] = date
    return _post(
        settings.KK_BASE_DEPARTURE, "/warehousedeparture/api/packageK/get-paginated-list", body
    )


def k_detail(k_id: str) -> dict:
    return _get(
        settings.KK_BASE_DEPARTURE,
        "/warehousedeparture/api/packageK/get-packageK-information-by-id",
        {"id": k_id},
    )


def k_history(code: str) -> dict:
    """K history dùng `_apikey` header, KHÔNG Bearer (doc E.5)."""
    if not settings.KK_PACKAGEK_APIKEY:
        raise KinkinError("Thiếu KK_PACKAGEK_APIKEY trong .env")
    return _get(
        settings.KK_BASE_WAREHOUSE,
        "/warehouseexport/api/packageK/get-history-by-code",
        {"code": code},
        custom_headers={"_apikey": settings.KK_PACKAGEK_APIKEY},
    )


# Lưu ý: API KHO ĐẾN (*.dion.vn) nằm ở module riêng app/integrations/khoden_client.py
# vì dùng identity + token KHÁC hệ vanchuyenkinkin.com này.
