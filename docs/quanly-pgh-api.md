# API tạo PGH — hệ THẬT `quanly.vanchuyenkinkin.com` (gộp Kho đến + VTP)

> Bóc từ trang thật `https://quanly.vanchuyenkinkin.com/vandon/phieu-giao-hang/create`
> (DevTools + đọc `_create-edit-phieu-giao-hang.js`), 2026-06-04. **Không submit/test.**

## Kiến trúc
- `quanly.vanchuyenkinkin.com` là **GATEWAY** (ASP.NET MVC + jQuery, theme Metronic), KHÔNG phải SPA.
- Mọi AJAX qua wrapper `httpService` → URL = **`systemURL + <path>`**, `systemURL = https://quanly.vanchuyenkinkin.com/`.
- **Auth: cookie `access_token=<JWT>`** (ĐÃ XÁC MINH qua header request thật — KHÔNG phải Authorization Bearer).
  JWT do `identityapi.vanchuyenkinkin.com` cấp (iss/client_id=Kinkin, aud gồm WarehouseExportService,
  scope Identity/KinkinCore/KinkinReport/WarehouseExport) — **CÙNG token `khoden_client._lay_token()` lấy**
  (password grant lexuantruong). → `app/integrations/quanly_client.py` gửi token này qua cookie để gọi gateway.
- **ĐÃ TÍCH HỢP:** tạo PGH route qua gateway (`quanly_client.tao_pgh`) → kho đến + VTP (partner*) trong 1 call.
- Gateway định tuyến theo **prefix** tới backend: `KhoDen/...`, `CommonKDN/...`, `vckk/...`, `menu/...`, `notification/...`, `tblProduct/...`, `DeliveryOrderPartnerTracking/...`, `printbarcode/...`, `reference/...`.
- Prefix `KhoDen/deliveryorders/api/` (gateway) ↔ tương ứng backend trực tiếp `warehouseexportapi.vanchuyenkinkin.com/warehouseexport/api/deliveryorders/` (mà `khoden_client.py` đang gọi). **Path action giống nhau.**

## ⭐ ĐIỂM CỐT LÕI: Tạo PGH kho đến + VTP = MỘT call
`POST KhoDen/deliveryorders/api/add-update-delivery` (hàm `AddUpdateDO(obj)`), tạo & sửa chung.
**VTP nhúng vào `orderInformation` qua các field `partner*`** — chọn "đối tác vận chuyển" = Viettel Post
(`deliveryPartnerId = 1002`) thì backend tạo luôn đơn VTP. Không có call VTP riêng từ FE.

```jsonc
{
  "isAddOrder": false, "isDraft": false, "isCreate": true, "isRotation": false,
  "warehouseId": <id>,
  "orderInformation": {
    // --- KHO ĐẾN ---
    "deliveryMethodId": <1 luân chuyển | 2 giao trực tiếp | ...>,
    "customerCode", "customerId", "customerName", "customerPhone", "customerType",
    "addressId": <id địa chỉ nhận>, "paymentMethodId", "note", "receivedDateTime",
    "totalWeight", "total",
    // --- VTP (chỉ set khi deliveryPartnerId == 1002 = Viettel Post) ---
    "deliveryPartnerId": 1002,
    "partnerOrderService": "<mã dịch vụ VTP>",     // = #MaDichVu_vtp (mA_DV_CHINH)
    "partnerOrderPayment": <người trả cước>,        // #LoaiVanDon_vtp
    "partnerMoneyCollection": <COD>,                // #SoTienThuHo_vtp
    "partnerProductPrice": <giá trị hàng>,          // #GiaTriHangHoa_vtp
    "partnerProductName": "<tên đơn>",              // #TenDonHang_vtp
    "partnerProductLength": <cm>, "partnerProductWidth": <cm>, "partnerProductHeight": <cm>,
    "incomeWarehousePhone", "incomeWarehouseAddress", "incomeWarehouseName"  // kho nhận
  },
  "packageDeliveryDtos": [
    { "codeTracking", "orderDetailId", "packageFId", "codeF" }   // các kiện F đã chọn
  ]
}
```
- `ViettelPostDeliveryPartnerId = 1002`. `totalWeight` = tổng cân các kiện F đã tích.
- **Câu hỏi mở quan trọng:** backend trực tiếp `warehouseexportapi.../deliveryorders/add-update-delivery`
  (qua `khoden_client.py`) có nhận các field `partner*` này để tạo VTP không? Nếu CÓ → Python tạo đồng thời 2 hệ chỉ bằng 1 call (cần verify ở phase test).

## Danh mục địa chỉ (cascade) — prefix `KhoDen/deliveryorders/api/`
| Cấp | Endpoint | Method | Ghi chú |
|---|---|---|---|
| Quốc gia | `nation/get-by-condition` | POST | select2 ajax |
| Tỉnh/TP | `provices/get-by-condition` | POST | ⚠️ typo "provices" |
| Quận/Huyện | `district/get-by-condition` | POST | body {provinceId} |
| Phường/Xã | `wards/get-by-condition` | POST | (KHÔNG typo như dion.vn) |
| Zipcode | `zipcode/get-by-condition` | POST | |
| **Tách địa chỉ** | `formatAddress?input=<text>` | GET | **parse địa chỉ tự do → tỉnh/huyện/xã** (rất hữu ích để tách `dia_chi_nguoi_nhan`) |

## Địa chỉ nhận của khách — `KhoDen/deliveryorders/api/DOReceiveAddress/`
- `get-data` (POST, body `{customerId}`) → list địa chỉ đã có của khách.
- `save-data` (POST) → lưu địa chỉ mới. ⚠️ **Hệ thật quanly dùng `DOReceiveAddress/save-data`** (khác hệ dion.vn dùng `deliveryAddress/save` — cần đối chiếu khi tạo địa chỉ).
- `set-default` (POST), `delete` (POST).

## Khách hàng
- `KhoDen/DeliveryOrders/api/get-customer-code` (POST, body `{customerCode:<term>, isParent}`)
  → `[{code, phone, displayName, paymentType, id(GUID), isFromVN2QT, isHaveWarehouseNotSameCountry, ...}]`.
- **`customer/api/list-server-side-parent`** (POST) — DataTables trang **Danh sách khách hàng**.
  Lọc bằng **`searchAll`** (KHÔNG phải `search.value`): khớp **mã + TÊN THẬT** (không khớp sđt),
  không có → `recordsFiltered:0` (⇒ "chưa có khách → tạo tài khoản"). Item: `{id(INT kinkinId, KHÔNG
  phải GUID), code, name(=TÊN THẬT), displayName(=mã), phone, paymentType, groupName, address, ...}`.
  Body tối thiểu: `{draw,columns:[…],start,length,search:{value:"",regex:false},searchAll:<term>,
  nguoiQuanLy:null,trangThaiHoatDong:"",bangGiaSanId:0}`. ⇒ tìm khách theo TÊN (get-customer-code &
  core get-list-customer-by-search chủ yếu theo mã); `id` INT nên cần resolve code→GUID qua core khi tạo PGH.

## Kiện F / K
- `KhoDen/DeliveryOrders/api/get-packageF-by-information` (POST) — tìm kiện F theo customerCode/F/K/tracking/MAWB.
- `KhoDen/DeliveryOrders/api/get-packageK-by-information` (POST) — tìm kiện K.
- `KhoDen/deliveryorders/api/get-list-product-by-packagek-id` (POST) — sản phẩm trong kiện K.
- `KhoDen/DeliveryOrders/api/get-bill-by-code` (POST) — bill/MAWB theo code.
- Item kiện F gồm: `mawb, billClosedDate, billDate, customerCode, codeF, codeKVK, codeTracking, departureWarehouseName, weight, statusName, packageFId, guid, orderDetailId, isChecked, productSpecialInformation[]`.

## VTP — đối tác vận chuyển & báo giá
- `KhoDen/DeliveryOrders/api/get-list-delivery-partner` (GET) → `[{id, name}]` (Viettel Post `id=1002`).
- `KhoDen/deliveryOrders/api/get-list-service` (POST) — **báo giá + DS dịch vụ VTP** (đổ vào `#MaDichVu_vtp`).
  Body (field kiểu VTP UPPERCASE):
  ```jsonc
  { "PRODUCT_WEIGHT", "PRODUCT_PRICE", "MONEY_COLLECTION",
    "PRODUCT_LENGTH", "PRODUCT_WIDTH", "PRODUCT_HEIGHT",
    "KhoHangId": <kinkinId kho nhận>,
    "SENDER_PROVINCE", "SENDER_DISTRICT",     // từ kho đến (warehouseInfo)
    "RECEIVER_PROVINCE", "RECEIVER_DISTRICT"  // từ địa chỉ nhận (selectedAddress)
  }
  ```
  Response item: `{mA_DV_CHINH (mã DV), teN_DICHVU (tên), thoI_GIAN (thời gian), giA_CUOC (giá cước)}`.
  → Gọi khi đổi dịch vụ/kích thước/giá trị và partner=VTP; điều kiện: có địa chỉ nhận + kho đến + tổng cân.
  - ✅ **ĐÃ XÁC MINH (2026-06-05)** — `SENDER_*`/`RECEIVER_*` là **`provinceKinKinId`/`districtKinKinId` (SỐ)**,
    KHÔNG phải GUID/tên (truyền GUID → `400 Object reference not set`; bỏ trống → `400 Nullable must have a value`).
    Lấy số này bằng `formatAddress?input=<địa chỉ text>` → trả `provinceKinKinId`/`districtKinKinId`.
    JS thật: `SENDER_*=warehouseInfo.provinceKinKinId` (từ `formatAddress(income-warehouse-address)`),
    `RECEIVER_*=selectedAddress.provinceKinkinId` (từ `DOReceiveAddress/get-data`). `KhoHangId`=kinkinId kho đến.
    `PRODUCT_WEIGHT` = tổng cân kiện F đã tích (raw, KHÔNG ×1000). → Đã wire: `quanly_client.format_address` +
    `bao_gia_vtp`; endpoint app `GET /pgh/kho-den/api/vtp-service`.

## Hình thức giao hàng (deliveryMethodId) — ✅ XÁC MINH LIVE `get-filter-method` (2026-06-05)
`1`=Luân Chuyển · `2`=Giao hàng trực tiếp · **`3`=Giao hàng qua đối tác** · `4`=Giao hàng tại kho · `0`=Tất cả (filter).
Đối tác `get-list-delivery-partner` → Viettel Post `id=1002`. Rule app: phương thức gửi sheet chứa "viettel"
→ mặc định method=3 + partner=1002 (`tao_pgh_kho_den.suy_ra_hinh_thuc`); còn lại → method=2.

## Kho
- `CommonKDN/KKWarehouses/api/list` (GET) → DS kho (có `kinkinId`).
- `KhoDen/DeliveryOrders/api/get-list-warehouse` (GET).

## Danh sách / chi tiết / khác (màn hình list)
- `KhoDen/DeliveryOrders/api/list-server-side` (POST) — datatable server-side.
- `.../get-filter-method`, `.../get-filter-status`, `.../get-filter-packageF-status` (POST) — bộ lọc.
- `.../delete-delivery?Id=<GUID>` (POST, body `{}`) — xóa PGH (từ chối nếu F đã xuất kho).
- `.../get-Delivery-By-Code` (GET) — autocomplete số chứng từ (trả mảng mã).
- `.../get-see-delivery-note` (POST) — chi tiết PGH.
- `.../get-account-by-name`, `.../get-lcd-by-delivery`, `.../stockout-list`, `.../export-excel*`.
- `DeliveryOrderPartnerTracking/api/list-get-partner-by-reference-code/` (GET) — tracking đơn VTP.
- `printbarcode/api/print-delivery-order` + `-pdf` — in phiếu.
- `tblProduct/api/update-hs-code` (PUT) — cập nhật HS code.
- `vckk/aspnetUser/api/get-info-logged-in-user` (GET) — user hiện tại.
- `reference/api/search` — tra cứu reference.

## So sánh với cách tích hợp của project (khoden_client.py)
- Project gọi **backend trực tiếp** (`warehouseexportapi.vanchuyenkinkin.com/warehouseexport/api/...`) bằng **OAuth `/connect/token`** (client Kinkin/KinkinAPP) — KHÁC gateway quanly (JWT localStorage).
- Action path tương đương → dùng lại được. Điểm MỚI cần thêm vào body `orderInformation`: cụm `partner*` + `deliveryPartnerId=1002` để tạo VTP đồng thời (nếu backend trực tiếp hỗ trợ — verify sau).
- Báo giá VTP: thêm `get-list-service`; tạo địa chỉ: cân nhắc `DOReceiveAddress/save-data` (hệ thật) vs `deliveryAddress/save`.
