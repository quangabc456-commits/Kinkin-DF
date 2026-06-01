# API endpoints — kiểm kê toàn hệ thống

Mục đích: 1 nguồn tham chiếu duy nhất khi port code sang Cloudflare Worker.
Liệt kê đầy đủ endpoint internal (Vercel/Next.js), upstream Kinkin, và
webhook outbound.

---

## A. Cron internal (Vercel — sẽ trở thành fallback sau khi cutover Worker)

| Method | Path | File | maxDuration | Schedule |
|---|---|---|---|---|
| GET | `/api/cron/sync` | [app/api/cron/sync/route.ts](../app/api/cron/sync/route.ts) | 60s | pg_cron `*/5 * * * *` |
| GET | `/api/cron/list-sync` | [app/api/cron/list-sync/route.ts](../app/api/cron/list-sync/route.ts) | 30s | pg_cron `*/2 * * * *` |

Mỗi route protect bằng `?secret=<CRON_SECRET>` (env).

- `/api/cron/sync` — "v11" detail-sync: multi-customer `/get-list` → queue PGH
  active (status whitelist) → `syncOnePgh` (F + XK + K) → push sheet 450HN →
  insert `sync_log` (source='cron').
- `/api/cron/list-sync` — "v1-list-only": chỉ upsert 7 cột cơ bản trong cửa sổ
  ±1d, không kéo F, mục đích trang điều phối / danh sách PGH luôn có phiếu mới.

## B. Admin (UI manual sync)

| Method | Path | File | Mục đích |
|---|---|---|---|
| POST | `/api/admin/pgh-sync/list` | [app/api/admin/pgh-sync/list/route.ts](../app/api/admin/pgh-sync/list/route.ts) | Get danh sách PGH 1 cửa sổ ngày (multi-customer parallel) |
| POST | `/api/admin/pgh-sync/run` | [app/api/admin/pgh-sync/run/route.ts](../app/api/admin/pgh-sync/run/route.ts) | Sync 1 batch ≤5 PGH (per-PGH timeout 12s, budget 35s) |
| GET | `/api/admin/pgh-sync/missing-f` | [app/api/admin/pgh-sync/missing-f/route.ts](../app/api/admin/pgh-sync/missing-f/route.ts) | Liệt kê PGH chưa có F nào |

Gated bằng `isAdminRequest()` (cookie Supabase Auth + role=ADMIN).

## C. User & Setup

| Method | Path | File | Mục đích |
|---|---|---|---|
| POST | `/api/setup` | [app/api/setup/route.ts](../app/api/setup/route.ts) | Chạy migrations + tạo admin đầu tiên (idempotent) |
| POST | `/api/users` | [app/api/users/route.ts](../app/api/users/route.ts) | Admin tạo user mới |
| PATCH | `/api/users/[id]` | [app/api/users/[id]/route.ts](../app/api/users/[id]/route.ts) | Sửa user (password / role / active) |
| DELETE | `/api/users/[id]` | [app/api/users/[id]/route.ts](../app/api/users/[id]/route.ts) | Xoá user |

## D. Debug (raw response Kinkin — public, chỉ trả response, không sửa DB)

| Method | Path | File | Mục đích |
|---|---|---|---|
| GET | `/api/debug/pgh` | [app/api/debug/pgh/route.ts](../app/api/debug/pgh/route.ts) | Raw `get-list` + `get-see-delivery-note` cho 1 PGH |
| GET | `/api/debug/k-vk` | [app/api/debug/k-vk/route.ts](../app/api/debug/k-vk/route.ts) | Raw K/VK/F (tự nhận diện prefix) |
| GET | `/api/debug/sync-log` | [app/api/debug/sync-log/route.ts](../app/api/debug/sync-log/route.ts) | 20 row `sync_log` gần nhất + meta |
| GET | `/api/debug/time-list` | [app/api/debug/time-list/route.ts](../app/api/debug/time-list/route.ts) | Đo `ms` per customer cho `/get-list` |

## D-bis. Lookup K/VK/F (frontend mobile/scan — cần login)

| Method | Path | File | Mục đích |
|---|---|---|---|
| GET | `/api/lookup/[code]` | [app/api/lookup/[code]/route.ts](../app/api/lookup/[code]/route.ts) | Auto-detect prefix → trả info + fs + history. F → trả parents (kId/kCode/vkId/vkCode). |

Query optional: `?fs=0` bỏ list F, `?history=0` bỏ history. Auth: bất kỳ user
đã login (không cần ADMIN).

---

## E. Upstream Kinkin (gọi từ `lib/kinkin/*` — Worker sẽ gọi trực tiếp)

Base URLs (override qua env `KK_BASE_*`):
- Identity: `https://identityapi.vanchuyenkinkin.com`
- Warehouse Export: `https://warehouseexportapi.vanchuyenkinkin.com`
- Warehouse Departure: `https://warehousedepartureapi.vanchuyenkinkin.com`

### E.1 Authentication

| Method | Endpoint | Mục đích |
|---|---|---|
| POST | `/connect/token` | Login OAuth2 password grant → JWT access_token (~1h) |

Body: `grant_type=password, client_id=Kinkin, client_secret=KinkinAPP,
scope='Identity KinkinCore KinkinReport offline_access WarehouseDeparture
WarehouseExport', username, password`.

### E.2 PGH (phiếu giao hàng) — Warehouse Export

| Method | Endpoint | Mục đích |
|---|---|---|
| POST | `/warehouseexport/api/deliveryorders/get-list` | List PGH theo `{ searchContent, warehouseId, customerCode, fromDate, toDate, page, pageSize }`. Note: `fromDate` = cận trên, `toDate` = cận dưới (ngược REST convention) |
| POST | `/warehouseexport/api/deliveryorders/get-see-delivery-note` | Detail PGH + danh sách F: `{ deliveryCode, isSee:true, warehouseId }` |
| GET | `/warehouseexport/api/deliveryorders/get-Delivery-By-Code?code=PGH...` | Detail by code (không cần warehouse scan, mới hơn) |

### E.3 Kiện F — Warehouse Export

| Method | Endpoint | Mục đích |
|---|---|---|
| POST | `/warehouseexport/api/packageF/common/get-list-paginate` | Tra F: `{ warehouseId, packageFName: 'F...', page, pageSize, ... }` |

### E.4 Kiện VK — Warehouse Export

| Method | Endpoint | Mục đích |
|---|---|---|
| POST | `/warehouseexport/api/packageVK/common/get-list-paginate` | Tìm VK theo code (cũng dùng làm "history" — lấy creationDate + creatorName) |
| POST | `/warehouseexport/api/packageVK/common/get-package-detail` | Chi tiết VK (cần `packageVkId` từ list) |

> Kinkin KHÔNG có endpoint history riêng cho VK. `getVkHistory()` trong
> [lib/kinkin/k-vk-api.ts](../lib/kinkin/k-vk-api.ts) extract creationDate +
> creatorName + status từ list-paginate.

### E.5 Kiện K — Warehouse Departure + Export

| Method | Endpoint | Mục đích |
|---|---|---|
| POST | `/warehousedeparture/api/packageK/get-paginated-list` | Tìm K trong `{wWareHouseId, code, month, year, date}` |
| GET | `/warehousedeparture/api/packageK/get-packageK-information-by-id?id=...` | Detail K (cần `id` từ list) |
| GET | `/warehouseexport/api/packageK/get-history-by-code?code=...` | Lịch sử K (Nhập kho / Xuất kho / ...). Header `_apikey: <KK_PACKAGEK_APIKEY>`, KHÔNG dùng Bearer token. Lưu ý base là **export** chứ không phải departure. |

### E.6 Stockout (XK) — Warehouse Export

Endpoint nội bộ trong [lib/kinkin/sync-pgh.ts](../lib/kinkin/sync-pgh.ts)
`fetchStockoutInfo(pghCode, warehouseId)`. Trả `latest_xk_code`, `latest_xk_at`,
`xk_status`, `xk_f_summary` (cột M, N, O, P trong sheet).

---

## F. Outbound webhook (Worker push sau khi sync)

| Method | URL | Body | Mục đích |
|---|---|---|---|
| POST | `<SHEET_WEBHOOK_URL>` (env) | `{ secret: <SHEET_WEBHOOK_SECRET>, rows: [[A..P], ...] }` | Apps Script doPost upsert tab `450HN` theo cột B (mã PGH) |

Apps Script source: [docs/apps-script-450hn-import.gs](apps-script-450hn-import.gs).
Push logic: [lib/kinkin/sheet-push.ts](../lib/kinkin/sheet-push.ts).

Gated bằng env: chưa set `SHEET_WEBHOOK_URL` + `SHEET_WEBHOOK_SECRET` → bỏ qua,
không call.

---

## Tổng kết theo runtime

```
┌──────────────────────────────────────────────────────────┐
│ Vercel Next.js (chạy 24/7)                               │
│  ├─ Cron /api/cron/sync (B) — enrich XK/K + push sheet   │
│  ├─ Admin UI manual (B)                                  │
│  ├─ User & Setup (C)                                     │
│  └─ Debug (D)                                            │
└──────────────────────────────────────────────────────────┘
                       │
                       ▼ đọc/ghi DB
              ┌────────────────────┐
              │ Supabase Postgres  │ ← Local cron ghi
              └────────────────────┘
                       ▲
                       │ ghi DB
┌──────────────────────────────────────────────────────────┐
│ Máy local Node + PM2 (cron */5 * * * * VN)              │
│  ├─ getToken (in-memory cache TTL 50min)                 │
│  ├─ resolveCustomers (env / Supabase / fallback-all)     │
│  ├─ listSyncBasic per customer (parallel 10) → E.2       │
│  ├─ syncManyPghParallel (cap 50/tick) → E.2              │
│  │  └─ SKIP best-effort XK/K (Vercel enrich riêng)       │
│  └─ INSERT sync_log (source='local-cron')                │
│  Script: scripts/sync-cron-local.mjs                     │
└──────────────────────────────────────────────────────────┘
                       │
                       ▼ HTTP
              ┌────────────────────┐
              │ Kinkin API (E.*)   │
              └────────────────────┘
```
