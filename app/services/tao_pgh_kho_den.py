"""Tạo PGH trên hệ KHO ĐẾN (*.dion.vn).

2 luồng địa chỉ người nhận:
  - "địa chỉ cũ": đã có addressId (từ deliveryAddress của khách) → dùng luôn.
  - "địa chỉ mới": tạo địa chỉ (DOReceiveAddress/save-data) → lấy addressId → tạo PGH.

Xem docs/kho-den-api.md cho chi tiết field.
"""
from __future__ import annotations

from typing import Any, Optional

from app.core.config import settings
from app.integrations import khoden_client as kc


class KhoDenServiceError(Exception):
    pass


def resolve_dia_danh(
    ten_tinh: str,
    ten_huyen: str,
    ten_xa: str,
    naction_id: str = kc.NATION_VIETNAM_ID,
) -> dict[str, Any]:
    """Map tên Tỉnh/Huyện/Xã → GUID qua API địa danh dion.vn (cascade)."""
    tinhs = kc.ds_tinh(naction_id)
    tinh = kc.tim_theo_ten(tinhs, ten_tinh)
    if not tinh:
        raise KhoDenServiceError(f"Không khớp Tỉnh: {ten_tinh!r}")

    huyens = kc.ds_huyen(tinh["id"])
    huyen = kc.tim_theo_ten(huyens, ten_huyen)
    if not huyen:
        raise KhoDenServiceError(f"Không khớp Quận/Huyện: {ten_huyen!r} (trong {tinh['name']})")

    xas = kc.ds_xa(huyen["id"])
    xa = kc.tim_theo_ten(xas, ten_xa)
    if not xa:
        raise KhoDenServiceError(f"Không khớp Phường/Xã: {ten_xa!r} (trong {huyen['name']})")

    return {
        "nationId": naction_id,
        "nationName": kc.NATION_VIETNAM_NAME,
        "provinceId": tinh["id"],
        "provinceName": tinh["name"],
        "districtId": huyen["id"],
        "districtName": huyen["name"],
        "wardId": xa["id"],
        "wardName": xa["name"],
    }


def _match_dia_chi(
    addrs: list[dict], receiver: str, phone: str, address: str, geo: dict
) -> Optional[dict]:
    """Tìm địa chỉ khớp (receiver + phone + address + wardId) trong danh sách của khách."""
    r, p, a = kc.chuan_hoa(receiver), (phone or "").strip(), kc.chuan_hoa(address)
    for d in addrs:
        if (
            kc.chuan_hoa(d.get("receiver")) == r
            and (d.get("phone") or "").strip() == p
            and kc.chuan_hoa(d.get("address")) == a
            and d.get("wardId") == geo.get("wardId")
        ):
            return d
    return None


def tao_dia_chi_moi(
    khach: dict,
    receiver: str,
    receive_phone: str,
    ten_tinh: str,
    ten_huyen: str,
    ten_xa: str,
    address: str,
) -> dict[str, Any]:
    """Tìm-hoặc-tạo địa chỉ nhận cho khách → trả {addressId, geo, tao_moi, raw}.

    save-data chỉ trả {data:true} (không có id) nên: nếu địa chỉ đã tồn tại thì tái dùng;
    nếu chưa thì tạo rồi fetch lại danh sách để lấy id.
    """
    geo = resolve_dia_danh(ten_tinh, ten_huyen, ten_xa)

    da_co = _match_dia_chi(
        kc.lay_dia_chi_cua_khach(khach["id"]), receiver, receive_phone, address, geo
    )
    if da_co:
        return {"addressId": da_co["id"], "geo": geo, "tao_moi": False, "raw": da_co}

    # Body theo đúng deliveryAddress/save (field `phone`, có typeId; gắn khách qua
    # customerId/customerCode). Xác minh từ UI thật.
    body = {
        "id": None,
        "typeId": 2,
        "customerId": khach.get("id"),
        "customerCode": khach.get("code"),
        "deliveryPointCode": None,
        "receiver": receiver,
        "phone": receive_phone,
        **geo,
        "address": address,
        "warehouseId": None,
    }
    resp = kc.tao_dia_chi(body)
    if not (isinstance(resp, dict) and resp.get("responseStatus")):
        raise KhoDenServiceError(f"Tạo địa chỉ thất bại. Resp: {str(resp)[:300]}")

    moi = _match_dia_chi(
        kc.lay_dia_chi_cua_khach(khach["id"]), receiver, receive_phone, address, geo
    )
    if not moi:
        raise KhoDenServiceError("Đã tạo địa chỉ nhưng không tìm lại được để lấy addressId.")
    return {"addressId": moi["id"], "geo": geo, "tao_moi": True, "raw": moi, "request": body}


def build_body_pgh(
    *,
    khach: dict,
    address_id: str,
    packages: list[dict],
    delivery_method_id: int = 2,
    payment_method_id: Optional[int] = None,
    customer_type: int = 2,
    note: str = "",
    received_date: Optional[str] = None,
    total_weight: float = 0,
    warehouse_id: Optional[int] = None,
    is_draft: bool = True,
) -> dict[str, Any]:
    """Build body cho deliveryorders/add-update-delivery.

    packages: list các dict {"packageFId": <GUID>, "codeTracking": <packageFCode GKA…>}.
    """
    if not packages:
        raise KhoDenServiceError("packages rỗng — cần ít nhất 1 kiện F.")
    wh = warehouse_id if warehouse_id is not None else int(settings.DEFAULT_KHO_DEN_ID or 5)
    pay = payment_method_id if payment_method_id is not None else (khach.get("paymentType") or 2)

    return {
        "isDraft": is_draft,
        "isCreate": True,
        "isRotation": False,
        "warehouseId": wh,
        "orderInformation": {
            "id": None,
            "deliveryMethod": None,
            "deliveryMethodId": delivery_method_id,
            "customerType": customer_type,
            "customerTypeName": None,
            "customerCode": khach.get("code"),
            "customerName": khach.get("name"),
            "customerPhone": khach.get("phone"),
            "customerId": khach.get("id"),
            "addressId": address_id,
            "addressDetail": None,
            "paymentMethod": None,
            "paymentMethodId": pay,
            "note": note,
            "receivedDateTime": received_date,
            "receivedDateTimeDetail": "",
            "warehousRearrives": None,
            "warehousRearrivesId": None,
            "createDate": None,
            "creator": None,
            "totalWeight": total_weight,
            "total": len(packages),
            "BillCloseDate": None,
            "MawId": None,
        },
        "packageDeliveryDtos": [
            {
                "codeTracking": p.get("codeTracking"),
                "orderDetailId": None,
                "packageFId": p.get("packageFId"),
            }
            for p in packages
        ],
    }


def tao_pgh_dia_chi_cu(
    *,
    customer_code: str,
    address_id: str,
    packages: list[dict],
    **kwargs,
) -> dict[str, Any]:
    """Luồng địa chỉ cũ: đã có addressId."""
    khach = kc.lay_customer_id(customer_code)
    if not khach:
        raise KhoDenServiceError(f"Không tìm thấy khách {customer_code!r}")
    body = build_body_pgh(khach=khach, address_id=address_id, packages=packages, **kwargs)
    resp = kc.tao_pgh(body)
    return {"resp": resp, "request": body, "khach": khach}


def tao_pgh_dia_chi_moi(
    *,
    customer_code: str,
    receiver: str,
    receive_phone: str,
    ten_tinh: str,
    ten_huyen: str,
    ten_xa: str,
    address: str,
    packages: list[dict],
    **kwargs,
) -> dict[str, Any]:
    """Luồng địa chỉ mới: tạo địa chỉ → lấy addressId → tạo PGH."""
    khach = kc.lay_customer_id(customer_code)
    if not khach:
        raise KhoDenServiceError(f"Không tìm thấy khách {customer_code!r}")
    dc = tao_dia_chi_moi(khach, receiver, receive_phone, ten_tinh, ten_huyen, ten_xa, address)
    body = build_body_pgh(khach=khach, address_id=dc["addressId"], packages=packages, **kwargs)
    resp = kc.tao_pgh(body)
    return {"resp": resp, "request": body, "khach": khach, "dia_chi": dc}
