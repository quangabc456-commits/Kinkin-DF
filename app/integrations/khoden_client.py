"""Client cho hệ KHO ĐẾN (*.dion.vn) — RIÊNG với kinkin_client (*.vanchuyenkinkin.com).

3 host (xem docs/kho-den-api.md):
  - identity  : KK_BASE_KHODEN_IDENTITY  /connect/token
  - core      : KK_BASE_KHODEN_CORE      /kinkincore/api/...   (khách, địa danh)
  - khoden    : KK_BASE_KHODEN           /warehouseexport/api/... (PGH, địa chỉ)

Token lấy bằng password grant với tài khoản KK_KHODEN_USERNAME/PASSWORD
(client Kinkin/KinkinAPP — KHÁC tài khoản aitool01 của hệ vanchuyenkinkin).
"""
from __future__ import annotations

import threading
import unicodedata
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import httpx

from app.core.config import settings


CLIENT_ID = "Kinkin"
CLIENT_SECRET = "KinkinAPP"
SCOPE = "Identity KinkinCore KinkinReport WarehouseExport offline_access"

# GUID hằng (xác nhận từ dữ liệu thật)
NATION_VIETNAM_ID = "3e629beb-3283-4ab0-8983-28166dbbbc1b"
NATION_VIETNAM_NAME = "VIETNAM"


class KhodenError(Exception):
    pass


_token_lock = threading.Lock()
_token_cache: dict[str, Any] = {"value": None, "expires_at": None}


def _co_cau_hinh() -> None:
    if not settings.KK_KHODEN_USERNAME or not settings.KK_KHODEN_PASSWORD:
        raise KhodenError(
            "Thiếu KK_KHODEN_USERNAME / KK_KHODEN_PASSWORD trong .env "
            "(tài khoản hệ kho đến *.dion.vn)."
        )


def _lay_token(force_refresh: bool = False) -> str:
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
            "username": settings.KK_KHODEN_USERNAME.strip(),
            "password": settings.KK_KHODEN_PASSWORD.strip(),
        }
        with httpx.Client(base_url=settings.KK_BASE_KHODEN_IDENTITY, timeout=30.0) as c:
            r = c.post(
                "/connect/token",
                data=body,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        if r.status_code != 200:
            raise KhodenError(f"connect/token {r.status_code}: {r.text[:300]}")
        data = r.json()
        token = data.get("access_token")
        if not token:
            raise KhodenError(f"connect/token không trả access_token: {data}")
        expires_in = int(data.get("expires_in") or 3600)
        _token_cache["value"] = token
        _token_cache["expires_at"] = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
        return token


def trang_thai_token() -> dict[str, Any]:
    exp = _token_cache["expires_at"]
    return {"co_token": bool(_token_cache["value"]), "het_han_luc": exp.isoformat() if exp else None}


def _headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {_lay_token()}", "Content-Type": "application/json"}


def _post(base: str, path: str, body: dict) -> dict:
    with httpx.Client(base_url=base, timeout=30.0) as c:
        r = c.post(path, json=body, headers=_headers())
    if r.status_code != 200:
        raise KhodenError(f"POST {path} {r.status_code}: {r.text[:400]}")
    return r.json()


def _get(base: str, path: str, params: dict) -> dict:
    with httpx.Client(base_url=base, timeout=30.0) as c:
        r = c.get(path, params=params, headers=_headers())
    if r.status_code != 200:
        raise KhodenError(f"GET {path} {r.status_code}: {r.text[:400]}")
    return r.json()


# ===== Core: khách hàng =====

def tim_khach(customer_code: str, customer_phone: str = "", is_parent: bool = False) -> list[dict]:
    """POST customer/get-list-customer-by-search → list khách (mỗi item có `id` = customerId)."""
    data = _post(
        settings.KK_BASE_KHODEN_CORE,
        "/kinkincore/api/customer/get-list-customer-by-search",
        {"customerCode": customer_code, "customerPhone": customer_phone, "isParent": is_parent},
    )
    return data.get("data") or []


def lay_customer_id(customer_code: str) -> Optional[dict]:
    """Trả về dict khách khớp customerCode (ưu tiên khớp chính xác code), hoặc None."""
    rows = tim_khach(customer_code)
    if not rows:
        return None
    code_norm = (customer_code or "").strip().upper()
    for r in rows:
        if (r.get("code") or "").strip().upper() == code_norm:
            return r
    return rows[0]


# ===== Core: địa danh (cascade) =====

def ds_tinh(naction_id: str = NATION_VIETNAM_ID) -> list[dict]:
    data = _post(
        settings.KK_BASE_KHODEN_CORE,
        "/kinkincore/api/Provinces/get-by-condition",
        {"nactionId": naction_id},
    )
    return data.get("data") or []


def ds_huyen(province_id: str) -> list[dict]:
    data = _post(
        settings.KK_BASE_KHODEN_CORE,
        "/kinkincore/api/District/get-by-condition",
        {"provinceId": province_id},
    )
    return data.get("data") or []


def ds_xa(district_id: str) -> list[dict]:
    # Lưu ý: endpoint có typo 'conditon' (đúng theo API thật)
    data = _post(
        settings.KK_BASE_KHODEN_CORE,
        "/kinkincore/api/Wards/get-by-conditon",
        {"districtId": district_id},
    )
    return data.get("data") or []


# ===== Kho đến: địa chỉ nhận =====

def ds_dia_chi(page: int = 1, page_size: int = 200, type_: Optional[int] = None) -> dict:
    """GET deliveryAddress/get-list. Trả nguyên {total, data:[...]}.
    (API không nhận filter theo khách — lọc client-side qua lay_dia_chi_cua_khach.)"""
    params = {"Type": type_ if type_ is not None else "null", "Page": page, "PageSize": page_size}
    return _get(
        settings.KK_BASE_KHODEN, "/warehouseexport/api/deliveryAddress/get-list", params
    )


def lay_dia_chi_cua_khach(customer_id: str, page_size: int = 500) -> list[dict]:
    """Lấy các địa chỉ điều phối đã có của 1 khách (lọc theo customerId)."""
    out: list[dict] = []
    page = 1
    while True:
        kq = ds_dia_chi(page=page, page_size=page_size)
        data = kq.get("data") or []
        out.extend(d for d in data if d.get("customerId") == customer_id)
        total = kq.get("total") or 0
        if page * page_size >= total or not data:
            break
        page += 1
    return out


def tao_dia_chi(body: dict) -> dict:
    """POST deliveryAddress/save → tạo/sửa địa chỉ. Trả {responseStatus, data:true}.

    Lưu ý: endpoint này CHỈ trả data:true (không có id). Lấy addressId bằng cách
    fetch lại deliveryAddress/get-list sau khi save. (DOReceiveAddress/save-data
    trong curl gốc KHÔNG persist — đã xác minh trên UI thật, dùng endpoint này.)
    """
    return _post(settings.KK_BASE_KHODEN, "/warehouseexport/api/deliveryAddress/save", body)


# ===== Kho đến: PGH =====

def tao_pgh(body: dict) -> dict:
    """POST deliveryorders/add-update-delivery → tạo/cập nhật PGH. Trả nguyên response."""
    return _post(
        settings.KK_BASE_KHODEN, "/warehouseexport/api/deliveryorders/add-update-delivery", body
    )


# ===== Tiện ích so khớp tên địa danh (cho luồng địa chỉ mới) =====

def chuan_hoa(s: Optional[str]) -> str:
    """Bỏ dấu, upper, gộp khoảng trắng — để so khớp tên tỉnh/huyện/xã."""
    if not s:
        return ""
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    s = s.replace("Đ", "D").replace("đ", "d")
    return " ".join(s.upper().split())


def tim_theo_ten(items: list[dict], ten: str) -> Optional[dict]:
    """Tìm item (tỉnh/huyện/xã) có name khớp `ten` (so chuẩn hoá, ưu tiên khớp đủ rồi chứa)."""
    t = chuan_hoa(ten)
    if not t:
        return None
    norm = [(chuan_hoa(it.get("name")), it) for it in items]
    for n, it in norm:
        if n == t:
            return it
    # bỏ tiền tố hành chính khi so
    def _strip(x: str) -> str:
        for p in ("QUAN ", "HUYEN ", "THI XA ", "THANH PHO ", "TP ", "PHUONG ", "XA ", "THI TRAN "):
            if x.startswith(p):
                return x[len(p):]
        return x
    ts = _strip(t)
    for n, it in norm:
        if _strip(n) == ts:
            return it
    for n, it in norm:
        if ts and (ts in n or _strip(n) in t):
            return it
    return None
