"""Client cho hệ KHO ĐẾN — hệ THẬT *.vanchuyenkinkin.com (trước đây TEST *.dion.vn).

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

# Client HTTP DÙNG CHUNG: giữ kết nối keep-alive theo từng host → tránh bắt tay TCP/TLS
# lại mỗi call (mỗi lần tạo httpx.Client mới = +100–300ms). httpx pool theo host, an toàn
# đa luồng (endpoint sync chạy trong threadpool). connect timeout ngắn để host chết fail nhanh.
_HTTP = httpx.Client(
    timeout=httpx.Timeout(30.0, connect=8.0),
    limits=httpx.Limits(max_keepalive_connections=20, max_connections=40, keepalive_expiry=60.0),
)

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
            "(tài khoản hệ kho đến *.vanchuyenkinkin.com — hệ THẬT; tài khoản dion.vn TEST không dùng được)."
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
        r = _HTTP.post(
            settings.KK_BASE_KHODEN_IDENTITY + "/connect/token",
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
    r = _HTTP.post(base + path, json=body, headers=_headers())
    if r.status_code != 200:
        raise KhodenError(f"POST {path} {r.status_code}: {r.text[:400]}")
    return r.json()


def _get(base: str, path: str, params: dict) -> dict:
    r = _HTTP.get(base + path, params=params, headers=_headers())
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


# ===== Core: quốc gia / kho / khách (bulk cho sync reference) =====

def ds_quoc_gia() -> list[dict]:
    """GET nactions/get-all → [{id, name}] (VIETNAM id = NATION_VIETNAM_ID)."""
    data = _get(settings.KK_BASE_KHODEN_CORE, "/kinkincore/api/nactions/get-all", {})
    return data.get("data") if isinstance(data, dict) else (data or [])


def ds_kho() -> list[dict]:
    """GET warehouse/get-list → [{id, name, code, ...}]."""
    data = _get(settings.KK_BASE_KHODEN_CORE, "/kinkincore/api/warehouse/get-list", {})
    return data.get("data") if isinstance(data, dict) else (data or [])


def ds_khach_all(page: int = 1, page_size: int = 500) -> dict:
    """POST customer/get-list → trang khách (bulk). Trả nguyên {data, total} (best-effort;
    body/envelope cần xác minh trên hệ thật)."""
    return _post(
        settings.KK_BASE_KHODEN_CORE,
        "/kinkincore/api/customer/get-list",
        {"page": page, "pageSize": page_size},
    )


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


# ===== Kho đến: kiện F (chọn lên PGH) =====

def ds_kien_f(
    customer_code: str,
    warehouse_id: Optional[int] = None,
    package_f_status: int = 0,
    package_f_name: str = "",
    page: int = 1,
    page_size: int = 200,
) -> list[dict]:
    """POST packageF/common/get-list-paginate → danh sách kiện F của khách.

    package_f_status=0 → mọi trạng thái (lọc/hiển thị client theo currentPackageFStatus).
    Item: {packageFId, packageFCode, packageFName(F…), currentPackageFStatus,
           packageFStatusName, packageFWeight, ...}. codeTracking lên PGH = packageFCode.
    """
    wh = warehouse_id if warehouse_id is not None else int(settings.DEFAULT_KHO_DEN_ID or 5)
    data = _post(
        settings.KK_BASE_KHODEN,
        "/warehouseexport/api/packageF/common/get-list-paginate",
        {
            "warehouseId": wh,
            "packageFStatus": package_f_status,
            "customerCode": customer_code,
            "packageFName": package_f_name,
            "packageFFilterDate": None,
            "page": page,
            "pageSize": page_size,
            "sortField": "",
            "sortOrder": "ASC",
        },
    )
    payload = data.get("data")
    if isinstance(payload, dict):
        return payload.get("items") or payload.get("data") or []
    return payload or []


# ===== Kho đến: PGH =====

def tao_pgh(body: dict) -> dict:
    """POST deliveryorders/add-update-delivery → tạo/cập nhật PGH. Trả nguyên response."""
    return _post(
        settings.KK_BASE_KHODEN, "/warehouseexport/api/deliveryorders/add-update-delivery", body
    )


def tim_pgh_theo_so_ct(code: str, warehouse_id: Optional[int] = None, page_size: int = 50) -> Optional[dict]:
    """Tìm PGH theo SỐ CHỨNG TỪ (vd 'PGH06022620F0ABB9') qua deliveryorders/get-list.

    Dùng `searchContent` = số chứng từ + dải ngày rộng. LƯU Ý get-list nhận ngày ĐẢO NGƯỢC
    (fromDate = mốc muộn, toDate = mốc sớm); để None hoặc thuận chiều sẽ trả rỗng. Trả item
    khớp đúng `code` (có 'id' = GUID nội bộ, 'statusName', ...), hoặc None.
    (get-Delivery-By-Code chỉ trả chuỗi mã cho autocomplete, không có id.)
    """
    wh = str(warehouse_id if warehouse_id is not None else (settings.DEFAULT_KHO_DEN_ID or 5))
    body = {
        "page": 1, "pageSize": page_size, "sortField": "", "sortOrder": "ASC",
        "customerType": None, "customerCodeFilter": None, "statusId": None,
        "searchContent": code, "creatorId": None, "warehouseId": wh,
        "packageFFilter": None, "deliveryMethodId": None, "typeDate": 1,
        "fromDate": "2100-01-01T00:00:00.000Z", "toDate": "2000-01-01T00:00:00.000Z",
    }
    data = _post(settings.KK_BASE_KHODEN, "/warehouseexport/api/deliveryorders/get-list", body)
    items = data.get("data") or []
    for it in items:
        if (it.get("code") or "") == code:
            return it
    return None


def xoa_pgh(delivery_order_id: str) -> dict:
    """Xóa PGH theo GUID nội bộ. POST deliveryorders/delete-delivery?Id=<GUID> (body rỗng).

    Trả {responseStatus, responseMess, data}. Lưu ý: hệ kho đến TỪ CHỐI xóa nếu kiện F
    của phiếu đã xuất kho ("Phiếu liên hàng này có kiện hàng đã được xuất kho!").
    """
    return _post(
        settings.KK_BASE_KHODEN,
        f"/warehouseexport/api/deliveryorders/delete-delivery?Id={delivery_order_id}",
        {},
    )


def xoa_pgh_theo_so_ct(code: str) -> dict:
    """Tiện ích: resolve số chứng từ -> GUID rồi xóa. Raise KhodenError nếu không tìm thấy.

    Trả {code, id, status, resp} với resp là response của delete-delivery.
    """
    it = tim_pgh_theo_so_ct(code)
    if not it:
        raise KhodenError(f"Không tìm thấy PGH số chứng từ {code!r} trên hệ kho đến.")
    return {
        "code": code,
        "id": it["id"],
        "status": it.get("statusName"),
        "resp": xoa_pgh(it["id"]),
    }


# ===== Kho đến: đối tác VTP + tra cứu màn hình tạo PGH =====
# (Bóc từ hệ thật quanly.vanchuyenkinkin.com — xem docs/quanly-pgh-api.md.
#  Trên backend trực tiếp, các path này nằm dưới /warehouseexport/api/deliveryorders/...)

def ds_doi_tac_vc() -> list[dict]:
    """GET deliveryorders/get-list-delivery-partner → [{id, name}] (Viettel Post id = 1002)."""
    data = _get(
        settings.KK_BASE_KHODEN,
        "/warehouseexport/api/deliveryorders/get-list-delivery-partner",
        {},
    )
    return data.get("data") if isinstance(data, dict) else (data or [])


def bao_gia_vtp(body: dict) -> list[dict]:
    """POST deliveryorders/get-list-service → danh sách dịch vụ VTP + giá cước.

    body (field kiểu VTP UPPERCASE): PRODUCT_WEIGHT, PRODUCT_PRICE, MONEY_COLLECTION,
    PRODUCT_LENGTH/WIDTH/HEIGHT, KhoHangId, SENDER_PROVINCE/DISTRICT, RECEIVER_PROVINCE/DISTRICT.
    Item trả về: {mA_DV_CHINH (mã DV), teN_DICHVU (tên), thoI_GIAN, giA_CUOC (giá cước)}.
    """
    data = _post(
        settings.KK_BASE_KHODEN,
        "/warehouseexport/api/deliveryorders/get-list-service",
        body,
    )
    return data.get("data") if isinstance(data, dict) else (data or [])


def tach_dia_chi(text: str) -> dict:
    """GET deliveryorders/formatAddress?input= → parse địa chỉ tự do → tỉnh/huyện/xã (best-effort)."""
    return _get(
        settings.KK_BASE_KHODEN,
        "/warehouseexport/api/deliveryorders/formatAddress",
        {"input": text},
    )


def tim_ma_khach(term: str, is_parent: Optional[bool] = None) -> list[dict]:
    """POST deliveryorders/get-customer-code → tra khách theo từ khoá (mã/sđt).

    Item: {code, phone, displayName, paymentType, id (GUID), isFromVN2QT, ...}.
    """
    body = {"customerCode": term, "isParent": is_parent}
    data = _post(
        settings.KK_BASE_KHODEN,
        "/warehouseexport/api/deliveryorders/get-customer-code",
        body,
    )
    return data.get("data") if isinstance(data, dict) else (data or [])


def tim_f_theo_thong_tin(body: dict) -> list[dict]:
    """POST deliveryorders/get-packageF-by-information → tìm kiện F theo customerCode/F/K/tracking/MAWB."""
    data = _post(
        settings.KK_BASE_KHODEN,
        "/warehouseexport/api/deliveryorders/get-packageF-by-information",
        body,
    )
    payload = data.get("data") if isinstance(data, dict) else data
    if isinstance(payload, dict):
        return payload.get("items") or payload.get("data") or []
    return payload or []


def ds_kien_f_kha_dung(customer_code: str) -> list[dict]:
    """Kiện F **CHƯA lên phiếu giao hàng** (khả dụng để chọn) — qua get-packageF-by-information.

    Endpoint này TỰ LỌC: F đã lên phiếu / đã xuất / đang giao / đã giao sẽ KHÔNG trả về
    (giống F-picker của trang quản lý). Chuẩn hoá field về CÙNG tên với ds_kien_f để template
    + token + build_body dùng chung, không phải sửa chỗ khác. (codeF=mã F, codeTracking=mã vận
    đơn, codeKVK=mã kiện K, weight=cân, statusName=trạng thái.)
    """
    rows = tim_f_theo_thong_tin(
        {"customerCode": customer_code, "packageFCode": "", "packageKCode": "",
         "codeTracking": "", "mawb": ""}
    )
    out: list[dict] = []
    for f in rows:
        out.append(
            {
                "packageFId": f.get("packageFId") or f.get("guid"),
                "packageFName": f.get("codeF") or f.get("packageFName"),
                "packageFCode": f.get("codeTracking") or f.get("packageFCode"),
                "packageFWeight": f.get("weight") if f.get("weight") is not None else f.get("packageFWeight"),
                "packageKCode": f.get("codeKVK") or f.get("packageKCode"),
                "mawb": f.get("mawb"),
                "billClosedDate": f.get("billClosedDate"),
                "billDate": f.get("billDate"),
                "customerCode": f.get("customerCode") or customer_code,
                "packageFStatusName": f.get("statusName") or f.get("packageFStatusName"),
                "currentPackageFStatus": f.get("currentPackageFStatus"),
                "orderDetailId": f.get("orderDetailId"),
                "departureWarehouseName": f.get("departureWarehouseName"),
            }
        )
    return out


def tim_k_theo_thong_tin(body: dict) -> list[dict]:
    """POST deliveryorders/get-packageK-by-information → tìm kiện K theo thông tin."""
    data = _post(
        settings.KK_BASE_KHODEN,
        "/warehouseexport/api/deliveryorders/get-packageK-by-information",
        body,
    )
    payload = data.get("data") if isinstance(data, dict) else data
    if isinstance(payload, dict):
        return payload.get("items") or payload.get("data") or []
    return payload or []


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
