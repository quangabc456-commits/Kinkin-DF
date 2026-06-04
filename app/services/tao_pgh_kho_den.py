"""Tạo PGH trên hệ KHO ĐẾN (*.vanchuyenkinkin.com — hệ THẬT; trước đây TEST *.dion.vn).

2 luồng địa chỉ người nhận:
  - "địa chỉ cũ": đã có addressId (từ deliveryAddress của khách) → dùng luôn.
  - "địa chỉ mới": tạo địa chỉ (DOReceiveAddress/save-data) → lấy addressId → tạo PGH.

Xem docs/kho-den-api.md cho chi tiết field.
"""
from __future__ import annotations

from typing import Any, Optional

from app.core.config import settings
from app.integrations import khoden_client as kc
from app.integrations import quanly_client as qc


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
        raise KhoDenServiceError(f"Không tìm thấy Tỉnh/Thành phố khớp: {ten_tinh}")

    huyens = kc.ds_huyen(tinh["id"])
    huyen = kc.tim_theo_ten(huyens, ten_huyen)
    if not huyen:
        raise KhoDenServiceError(f"Không tìm thấy Quận/Huyện khớp: {ten_huyen} (thuộc {tinh['name']})")

    xas = kc.ds_xa(huyen["id"])
    xa = kc.tim_theo_ten(xas, ten_xa)
    if not xa:
        raise KhoDenServiceError(f"Không tìm thấy Phường/Xã khớp: {ten_xa} (thuộc {huyen['name']})")

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
        raise KhoDenServiceError("Lưu địa chỉ chưa thành công. Vui lòng kiểm tra lại thông tin địa chỉ rồi thử lại.")

    moi = _match_dia_chi(
        kc.lay_dia_chi_cua_khach(khach["id"]), receiver, receive_phone, address, geo
    )
    if not moi:
        raise KhoDenServiceError("Đã lưu địa chỉ nhưng chưa lấy lại được. Vui lòng thử lại.")
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
    vtp: Optional[dict] = None,
) -> dict[str, Any]:
    """Build body cho deliveryorders/add-update-delivery.

    packages: list các dict {"packageFId": <GUID>, "codeTracking": <packageFCode GKA…>}.
    vtp: nếu có → tạo đồng thời đơn Viettel Post (1-call) bằng cách nhồi cụm `partner*`
         vào orderInformation. Các key dùng: service, payment, cod, price, product_name,
         length, width, height, warehouse_phone, warehouse_address, warehouse_name,
         partner_id (mặc định settings.VIETTELPOST_PARTNER_ID). Xem docs/quanly-pgh-api.md.
    """
    if not packages:
        raise KhoDenServiceError("Chưa có kiện F nào để lên phiếu (cần ít nhất 1 kiện).")
    wh = warehouse_id if warehouse_id is not None else int(settings.DEFAULT_KHO_DEN_ID or 5)
    pay = payment_method_id if payment_method_id is not None else (khach.get("paymentType") or 2)

    order_info: dict[str, Any] = {
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
    }

    if vtp:
        # Đồng thời tạo đơn Viettel Post — backend kho đến nhận cụm partner* (xem hệ thật quanly).
        order_info.update(_vtp_partner_fields(vtp))

    return {
        "isDraft": is_draft,
        "isCreate": True,
        "isRotation": False,
        "warehouseId": wh,
        "orderInformation": order_info,
        "packageDeliveryDtos": [
            {
                "codeTracking": p.get("codeTracking"),
                "orderDetailId": None,
                "packageFId": p.get("packageFId"),
            }
            for p in packages
        ],
    }


def _to_int(v: Any, default: int = 0) -> int:
    try:
        return int(str(v).replace(",", "").strip())
    except (TypeError, ValueError):
        return default


def _vtp_partner_fields(vtp: dict) -> dict[str, Any]:
    """Map dict vtp (từ form) → các field partner* của orderInformation."""
    return {
        "deliveryPartnerId": vtp.get("partner_id") or settings.VIETTELPOST_PARTNER_ID,
        "partnerOrderService": vtp.get("service"),
        "partnerOrderPayment": _to_int(vtp.get("payment"), 0),
        "partnerMoneyCollection": _to_int(vtp.get("cod"), 0),
        "partnerProductPrice": _to_int(vtp.get("price"), 0),
        "partnerProductName": (vtp.get("product_name") or "").strip() or None,
        "partnerProductLength": _to_int(vtp.get("length"), 0),
        "partnerProductWidth": _to_int(vtp.get("width"), 0),
        "partnerProductHeight": _to_int(vtp.get("height"), 0),
        "incomeWarehousePhone": vtp.get("warehouse_phone"),
        "incomeWarehouseAddress": vtp.get("warehouse_address"),
        "incomeWarehouseName": vtp.get("warehouse_name"),
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
        raise KhoDenServiceError(f"Không tìm thấy khách hàng {customer_code}")
    body = build_body_pgh(khach=khach, address_id=address_id, packages=packages, **kwargs)
    resp = qc.tao_pgh(body)  # tạo qua gateway quanly → kho đến + VTP (partner*) trong 1 call
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
        raise KhoDenServiceError(f"Không tìm thấy khách hàng {customer_code}")
    dc = tao_dia_chi_moi(khach, receiver, receive_phone, ten_tinh, ten_huyen, ten_xa, address)
    body = build_body_pgh(khach=khach, address_id=dc["addressId"], packages=packages, **kwargs)
    resp = qc.tao_pgh(body)  # tạo qua gateway quanly → kho đến + VTP (partner*) trong 1 call
    return {"resp": resp, "request": body, "khach": khach, "dia_chi": dc}
