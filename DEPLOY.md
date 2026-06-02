# Deploy lên Vercel + Supabase (Free tier)

Tài liệu này hướng dẫn deploy app Kinkin PGH lên Vercel + Supabase miễn phí. Đã bỏ qua phần background sync (chạy local). Production chỉ phục vụ UI + lookup Kinkin + Apps Script webhook (passthrough).

## Phase 1 — Supabase Postgres

### 1.1 Tạo project
1. Vào <https://supabase.com/dashboard> → **New project**.
2. Đặt tên: `kinkin-df` (hoặc tên bất kỳ — Supabase project độc lập với Vercel), region **Singapore (ap-southeast-1)** (gần VN nhất).
3. Sinh password mạnh — **lưu lại, không paste vào AI**.
4. Plan: **Free** (500MB DB, đủ dùng).
5. Bấm Create → đợi ~2 phút.

### 1.2 Lấy connection string
1. Vào project → ⚙️ **Settings** → **Database** → **Connection string**.
2. Chọn **Transaction Pooler** (port 6543) — bắt buộc cho serverless.
3. Copy URL dạng: `postgresql://postgres.xxxxx:[PASSWORD]@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres`
4. Thay `[PASSWORD]` bằng password ở bước 1.1, thêm `?sslmode=require`.
5. Đổi `postgresql://` thành `postgresql+psycopg://` cho SQLAlchemy.

Kết quả ví dụ:
```
postgresql+psycopg://postgres.abcd1234:MyPass123@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require
```

### 1.3 Chạy migration từ máy local

```powershell
cd "c:\VScode\Kinkin - DF"
# Tạm thay DATABASE_URL trong .env, hoặc set inline:
$env:DATABASE_URL = "postgresql+psycopg://postgres.xxxxx:[PASSWORD]@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require"
.\.venv\Scripts\python.exe -m alembic upgrade head
```

Phải thấy:
```
INFO  [alembic.runtime.migration] Running upgrade -> 0001_initial
INFO  [alembic.runtime.migration] Running upgrade 0001_initial -> 0002_tai_khoan_kinkin
```

### 1.4 (Tuỳ chọn) Backfill data từ local sang Supabase

Nếu muốn copy data từ local Docker Postgres sang Supabase:
```powershell
# Dump từ local
docker exec kinkin_pgh_db pg_dump -U postgres -d kinkin_pgh --data-only --column-inserts > local-data.sql

# Restore vào Supabase (dùng psql trực tiếp, port 5432)
$env:PGPASSWORD = "<supabase_password>"
psql -h db.xxxxx.supabase.co -U postgres -d postgres -f local-data.sql
```

## Phase 2 — Sinh `GOOGLE_CREDS_JSON_B64`

Vercel không có file system riêng cho creds → mã hoá base64 file `BOT- DF.json` thành 1 chuỗi env var.

```powershell
cd "c:\VScode\Kinkin - DF"
python -c "import base64; print(base64.b64encode(open('BOT- DF.json','rb').read()).decode())"
```

Copy toàn bộ chuỗi (dài ~3000 ký tự) — sẽ paste vào Vercel ở Phase 3.

## Phase 3 — Vercel deploy

### 3.1 Cài Vercel CLI (1 lần)
```powershell
npm install -g vercel@latest
vercel login
```

### 3.2 Link project
```powershell
cd "c:\VScode\Kinkin - DF"
vercel link
```
Trả lời: Set up `c:\VScode\Kinkin - DF`? → **Y**, scope → `kin-kin`, link tới existing project → **Y** (chọn `kinkin-df`), root directory → `.`

> **Lưu ý**: Project ở team `kin-kin`, canonical domain **`kinkinlogistics-vtp.vercel.app`** (domain duy nhất đang dùng). Domain cũ `kinkin-df.vercel.app` đã bỏ — có thể xoá thẳng trong Vercel dashboard.

### 3.3 Set env vars
Chạy từng lệnh sau, hoặc làm 1 lượt trên dashboard <https://vercel.com/dashboard/[project]/settings/environment-variables>:

```powershell
# Database (Supabase pooler URL)
vercel env add DATABASE_URL production
# Paste: postgresql+psycopg://postgres.xxxxx:[PWD]@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require

# Google creds (base64 từ Phase 2)
vercel env add GOOGLE_CREDS_JSON_B64 production
# Paste chuỗi base64 dài

# Sheet
vercel env add SHEET_ID production
# Paste: 1S9FtklMhj6rKZmrtYx3jIKBz_xEDNrNYST0khlb1rB0

# Kinkin
vercel env add KK_USERNAME production
vercel env add KK_PASSWORD production
vercel env add KK_WAREHOUSE_IDS production    # 1,2,3,4,5,6,7,8,9,10
vercel env add KK_CUSTOMER_CODE production    # 450HN-GENKIN
vercel env add KK_PACKAGEK_APIKEY production

# Fernet (sinh mới hoặc copy từ local)
vercel env add FERNET_KEY production

# Tắt sync UI trên production
vercel env add ENABLE_SYNC_UI production
# Value: false
```

### 3.4 Deploy

```powershell
vercel --prod
```

Sau ~1 phút sẽ có URL: `https://kinkinlogistics-vtp.vercel.app` (canonical domain ở team `kin-kin`). Domain cũ `kinkin-df.vercel.app` không còn dùng.

## Phase 4 — Verify production

```powershell
$URL = "https://kinkinlogistics-vtp.vercel.app"
curl "$URL/health"                                # {"status":"ok"}
curl "$URL/api/kinkin/lookup/F1078805" | python -m json.tool
```

Mở browser: `https://kinkinlogistics-vtp.vercel.app/cau-hinh/` → phải thấy:
- Status Kinkin xanh "Đã cấu hình"
- Card sync hiển thị "⏸ Sync API tạm dừng" (vì `ENABLE_SYNC_UI=false`)

## Phase 5 — Workflow chạy hằng ngày (Hybrid)

| Việc | Chạy ở đâu |
|---|---|
| User truy cập UI, click code → modal | **Vercel** |
| Apps Script webhook → /webhook/sheet-changed | **Vercel** (bypass nếu ENABLE_SYNC_UI=false) |
| `python -m app.cli.sync --sheet 25-05-26` | **Máy local** với `DATABASE_URL` trỏ Supabase |
| `python -m app.cli.sync --all` | **Máy local** lần lượt khi cần backfill |
| `python -m app.cli.seed_dia_danh` | **Máy local** (chạy 1 lần ban đầu) |

Để máy local sync tự động:
1. Mở **Task Scheduler** (Windows)
2. Tạo Task chạy mỗi 5 phút: `c:\VScode\Kinkin - DF\.venv\Scripts\python.exe -m app.cli.sync --all --from-date <today>`
3. Set DATABASE_URL trong env của task → trỏ Supabase

## Troubleshooting

**"connection limit exceeded"** trên Supabase free → dùng URL pooler (port 6543) không phải direct (5432).

**Vercel build timeout** → check `vercel.json` `maxLambdaSize: 50mb`. Nếu vượt → loại bỏ deps lớn trong requirements.txt.

**Cold start chậm** → bình thường lần đầu sau idle. Fluid Compute warm sau request đầu.

**Lookup trả 500** → check Vercel logs: `vercel logs <deployment-url>`. Thường do thiếu env var.

**Supabase auto-pause sau 1 tuần** → free tier policy. Resume thủ công ở Dashboard hoặc upgrade Pro $25/m.
