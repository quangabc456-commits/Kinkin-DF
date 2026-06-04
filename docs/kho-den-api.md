# API Kho đến (hệ `*.dion.vn`) — tham chiếu tạo PGH

> Bóc từ trang thật `https://khoden-kinkin.dion.vn` (DevTools Network), ngày 2026-06-02.
> **Quan trọng:** Kho đến chạy trên **hệ API riêng `*.dion.vn`**, KHÁC hệ hiện cấu hình
> (`*.vanchuyenkinkin.com`). Phải dùng đúng host + token của hệ này.

## Hosts

| Vai trò | Host | Ghi chú |
|---|---|---|
| Identity (token) | `https://identity-kinkin.dion.vn` | `/connect/token` — JWT `iss=identity-kinkin.dion.vn`, `client_id=Kinkin`, scope `Identity KinkinCore KinkinReport WarehouseExport` |
| Core (khách, địa danh) | `https://apicore-kinkin.dion.vn` | prefix `/kinkincore/api` |
| Kho đến (PGH, địa chỉ) | `https://apikhoden-kinkin.dion.vn` | prefix `/warehouseexport/api` |

Tất cả request gắn header `Authorization: Bearer <token>`.

## 1. Tra khách → customerId

`POST apicore-kinkin.dion.vn/kinkincore/api/customer/get-list-customer-by-search`

Body: `{"customerCode":"093HN-VAT","customerPhone":"","isParent":false}`

Response `data[0]`:
```json
{"id":"8b440b00-b67f-4eba-9ed3-b18907519797","kinkinId":2549,"code":"093HN-VAT",
 "name":"093HN-VAT","phone":"093","address":"...","paymentType":2,"groupName":"FOB"}
```
→ **customerId = data[0].id**, customerPhone = `phone`, paymentMethodId ~ `paymentType`.
`isParent` = (Loại "Cha"→true / "Con"→false). customerType: Cha/Con.

## 2. Danh sách địa chỉ đã có của khách → addressId (luồng "địa chỉ cũ")

`GET apikhoden-kinkin.dion.vn/warehouseexport/api/deliveryAddress/get-list?Type=null&Page=1&PageSize=10`
(lọc theo khách: dùng các tham số/`customerId` — cần xác nhận thêm; hiện trả toàn bộ rồi lọc client theo `customerCode`/`customerId`).

Response `data[i]`:
```json
{"id":"badb4840-...","typeId":2,"customerId":"...","customerCode":"238HN",
 "receiver":"Trần An Khương","phone":"0982357919",
 "nationId":"3e629beb-...","nationName":"VIETNAM",
 "provinceId":"4e38e3af-...","provinceName":"Hà Nội",
 "districtId":"cb4a7589-...","districtName":"QUẬN HÀ ĐÔNG",
 "wardId":"ff1ad4ea-...","wardName":"KIẾN HƯNG",
 "address":"...", "deliveryPointCode":"94","isActive":true}
```
→ **addressId = id**. Có sẵn đủ nation/province/district/ward + receiver/phone.

## 3. Địa danh (luồng "địa chỉ mới") — cascade

| Cấp | Endpoint (POST, host core) | Body | Item trả về |
|---|---|---|---|
| Quốc gia | `/kinkincore/api/nactions/get-all` (GET) | — | `{id, name}` |
| Tỉnh | `/kinkincore/api/Provinces/get-by-condition` | `{"nactionId":"<GUID>"}` | `{id, name, code, nactionId}` |
| Quận/huyện | `/kinkincore/api/District/get-by-condition` | `{"provinceId":"<GUID>"}` | `{id, name, code, provinceId}` |
| Phường/xã | `/kinkincore/api/Wards/get-by-conditon` ⚠️typo | `{"districtId":"<GUID>"}` | `{id, name, code, districtId}` |

GUID hằng: VIETNAM `3e629beb-3283-4ab0-8983-28166dbbbc1b`; Hà Nội `4e38e3af-cd80-4b42-856a-05374ba75c57`;
QUẬN LONG BIÊN `1f5abb06-f9f7-4af6-950e-f644bc35cc37`.
→ Map địa chỉ text của đơn → name → id từng cấp (đối chiếu không dấu/HOA).

## 4. Tạo địa chỉ mới (luồng "địa chỉ mới", bước 1) — ĐÃ XÁC MINH

⚠️ Dùng **`POST apikhoden-kinkin.dion.vn/warehouseexport/api/deliveryAddress/save`**
(KHÔNG phải `DOReceiveAddress/save-data` trong curl gốc — endpoint đó trả `data:true`
nhưng **KHÔNG persist**, đã kiểm chứng).

Body (field `phone`, có `typeId`, gắn khách qua customerId/customerCode):
```json
{"id":null,"typeId":2,"customerId":"<GUID>","customerCode":"093HN-VAT",
 "deliveryPointCode":null,"receiver":"...","phone":"09xxxxx",
 "nationId","nationName","provinceId","provinceName","districtId","districtName",
 "wardId","wardName","address":"...","warehouseId":null}
```
Response: `{"responseStatus":true,"data":true}` — **không trả id**.
→ Lấy `addressId` bằng cách **fetch lại `deliveryAddress/get-list`** rồi lọc theo
customerId + so khớp receiver/phone/address/wardId (xem `tao_dia_chi_moi` trong service).

## 4b. Danh sách kiện F (để lấy packageFId + codeTracking)

`POST apikhoden-kinkin.dion.vn/warehouseexport/api/packageF/common/get-list-paginate`
Body: `{warehouseId:5, packageFStatus:0, customerCode, packageFName, packageFFilterDate:null, page, pageSize, sortField:"", sortOrder:"ASC"}`
Item: `{packageFId, packageFCode, packageFName(F…), customerCode, wareHouseId, currentPackageFStatus, packageFStatusName, packageFWeight}`
→ **codeTracking = packageFCode** (thường là số, vd `623036563763`); **packageFId** = GUID.
`currentPackageFStatus`: 2=Chờ xử lý tại kho đến, 3=Đã chia hàng, 8=Đang giao, 10=Hoàn thành.
F lên PGH mới phải **đang tồn ở kho đến (chưa giao)**.

## 5. Tạo PGH

`POST apikhoden-kinkin.dion.vn/warehouseexport/api/deliveryorders/add-update-delivery`
Body chính:
```
isDraft, isCreate:true, isRotation:false, warehouseId:5,
orderInformation:{ deliveryMethodId, customerType, customerCode, customerName,
  customerPhone, customerId, addressId, paymentMethodId, note, receivedDateTime,
  totalWeight, total, ... },
packageDeliveryDtos:[{ codeTracking:<packageFCode GKA…>, orderDetailId:null, packageFId:<GUID> }]
```
- `customerId` ← (1); `addressId` ← (2) hoặc id trả từ (4); `packageFId`/`packageFCode` ← cache F.
- `deliveryMethodId`: 2 = Giao hàng trực tiếp (UI có: Luân chuyển / Giao trực tiếp / Qua đối tác / Tại kho).

## 6. Xóa PGH — ĐÃ XÁC MINH (từ bundle JS trang thật)

`POST apikhoden-kinkin.dion.vn/warehouseexport/api/deliveryorders/delete-delivery?Id=<deliveryOrderId>`
Body rỗng `{}`. Header `Authorization: Bearer <token>`.

Bóc từ `main.*.js`:
```js
deleteDeliveryNote(t){ return this.http.post(this.wareHouseApiEndpoint+`/deliveryorders/delete-delivery?Id=${t}`,{}) }
```
- `Id` = **GUID nội bộ của PGH** (KHÔNG phải số chứng từ `PGH06022620F0ABB9`).
- vd PGH06022620F0ABB9 (bản nháp test) → Id = `548dfc4b-57c2-42dd-b08b-db3eba0fa1cc`.
- **Quy tắc nghiệp vụ:** API từ chối nếu kiện F của phiếu đã xuất kho →
  `{responseStatus:false, responseMess:"Phiếu liên hàng này có kiện hàng đã được xuất kho!"}`.
  Chỉ xóa được phiếu mà F còn tồn (vd bản nháp chưa xuất).

### Resolve số chứng từ → GUID
- `GET deliveryorders/get-Delivery-By-Code?code=<code>` chỉ trả **mảng chuỗi mã** (autocomplete),
  KHÔNG có id → không dùng để lấy GUID.
- Dùng `POST deliveryorders/get-list` với `searchContent=<số chứng từ>` (field `id` mỗi item = GUID).
  ⚠️ get-list nhận ngày **ĐẢO NGƯỢC**: `fromDate` = mốc muộn, `toDate` = mốc sớm (thuận chiều/None → rỗng).
  Hoặc trang chi tiết có call `auditlog/get-audit-log?resourceId=<GUID>`.

### Hàm dùng lại (`app/integrations/khoden_client.py`)
`tim_pgh_theo_so_ct(code)` → item (có `id`); `xoa_pgh(id)` → delete-delivery; `xoa_pgh_theo_so_ct(code)` → resolve+xóa.

## Phân loại UI (tham khảo từ trang thật)
Trạng thái F: Chờ nhập / Nhập kho / Chia hàng / Lưu kho / Đã xuất…
HT giao hàng: **Luân Chuyển / Giao hàng trực tiếp / Giao hàng qua đối tác / Giao hàng tại kho**.

> Token VTP đã chuyển vào `.env` (`VTP_SECRET_TOKEN`) — KHÔNG để trong file tài liệu (tránh lộ khi commit).