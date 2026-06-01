# Kinkin - Hệ thống quản lý PGH ViettelPost (Local Demo)

Hệ thống đọc dữ liệu trả hàng từ Google Sheet `(NEW) 450HN - GENKIN - THÔNG TIN TRẢ HÀNG`, lưu vào PostgreSQL, cho phép nhân viên bấm "Chốt" để tự gọi API ViettelPost tạo phiếu giao hàng (PGH), nhận webhook hành trình từ VTP.

## Stack

- Python 3.12
- PostgreSQL 16 (Docker)
- FastAPI + Jinja2 (UI nội bộ)
- SQLAlchemy 2 + Alembic
- gspread (Google Sheets)
- httpx (gọi VTP)

## Bước chạy lần đầu

### 1. Cài Docker Desktop

Tải từ <https://www.docker.com/products/docker-desktop>, cài rồi restart máy. Mở Docker Desktop để đảm bảo daemon đang chạy.

### 2. Khởi động Postgres

```powershell
cd "c:\VScode\Kinkin - DF"
docker compose up -d
docker compose ps    # phải thấy postgres "healthy"
```

### 3. Tạo Python venv + cài dependencies

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Tạo file `.env`

```powershell
Copy-Item .env.example .env
# Sinh FERNET_KEY rồi paste vào .env
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Mở `.env`, paste giá trị `FERNET_KEY=...` vừa sinh.

### 5. Chạy migration tạo schema

```powershell
$env:PYTHONIOENCODING="utf-8"
alembic upgrade head
```

### 6. Seed danh mục địa danh từ VTP (1 lần, ~5-10 phút)

```powershell
python -m app.cli.seed_dia_danh
```

### 7. Sync 1 sheet thử

```powershell
python -m app.cli.sync --sheet 25-05-26
# Hoặc sync tất cả sheet dd-mm-yy (chậm hơn, ~5 phút cho 170 sheet)
python -m app.cli.sync --all
# Hoặc chỉ sync từ ngày nào trở đi
python -m app.cli.sync --all --from-date 2026-01-01
```

### 8. Tạo 1 tài khoản VTP (chế độ dev)

Mở `psql` (hoặc DBeaver/pgAdmin) và chạy:

```sql
INSERT INTO tai_khoan_vtp (ten_hien_thi, username, secret_token, mac_dinh, kich_hoat, moi_truong)
VALUES ('Test Dev', '0382678080', 'DAN_SECRET_TOKEN_LAY_TU_TRANG_VTP', true, true, 'development');
```

> Secret token lấy từ trang `https://partnerdev.viettelpost.vn/cau-hinh-tai-khoan` → "Thêm mới token" → OTP → copy.
> Nếu chỉ có user/password thì để `secret_token = NULL`, thêm `password_enc` bằng hàm `app.security.ma_hoa("matkhau")`.

### 9. Chạy app

```powershell
python -m app.main
# hoặc: uvicorn app.main:app --reload
```

Mở <http://127.0.0.1:8000> → thấy bảng vận đơn Viettel chờ chốt → bấm "Chốt".

### 10. (Tuỳ chọn) Expose webhook cho VTP gọi về

```powershell
# Cài ngrok (https://ngrok.com/download), authtoken, rồi:
ngrok http 8000
# Copy URL https://xxx.ngrok.io + path /webhook/vtp
# Đăng ký URL này tại trang VTP partner → Cấu hình tài khoản → Webhook
# Sao chép Secret parameters → cập nhật vào tai_khoan_vtp.webhook_secret
```

## Cấu trúc thư mục (MVC)

```
app/
├── main.py                       # Entrypoint: tạo FastAPI app, mount static, include routers
│
├── core/                         # Infrastructure
│   ├── config.py                 # pydantic-settings (đọc .env)
│   ├── db.py                     # SQLAlchemy engine, session
│   ├── security.py               # Fernet encrypt/decrypt
│   └── templates.py              # Jinja2Templates shared instance
│
├── models/                       # M — SQLAlchemy ORM
│   ├── base.py                   # DeclarativeBase
│   ├── du_lieu_sheet.py
│   ├── phieu_giao_hang.py
│   ├── hanh_trinh_pgh.py
│   ├── tai_khoan_vtp.py
│   ├── dia_danh.py               # 3 bảng tỉnh/huyện/xã
│   └── audit.py                  # log_dong_bo_sheet, log_api_vtp, cau_hinh
│
├── views/                        # V — Jinja2 templates
│   ├── base.html
│   ├── pgh/
│   │   ├── danh_sach.html        # Bảng vận đơn Viettel
│   │   └── chi_tiet.html         # Chi tiết 1 PGH
│   └── cau_hinh/
│       └── index.html            # Trang cài đặt (bot, sheet, apps script, sync)
│
├── controllers/                  # C — Routes FastAPI
│   ├── pgh_controller.py         # GET /, POST /chot/{id}, GET /pgh/{id}
│   ├── cau_hinh_controller.py    # GET /cau-hinh/, POST sheet/sync/rotate-secret
│   └── webhook_controller.py     # POST /webhook/vtp, /webhook/sheet-changed
│
├── services/                     # Business logic (giữa Controllers & Models)
│   ├── sheet_sync.py             # Parse + upsert sheet → DB
│   ├── sheet_writeback.py        # Ghi PGH ngược về sheet
│   ├── seed_dia_danh.py          # Cache tỉnh/huyện/xã từ VTP
│   ├── dia_chi_lookup.py         # Text địa chỉ → ID
│   ├── apps_script.py            # Sinh Apps Script template
│   └── chot_pgh.py               # Orchestrator: dòng sheet → PGH qua VTP API
│
├── integrations/                 # External clients
│   ├── google_sheets.py          # gspread auth helper
│   └── vtp_client.py             # Wrapper API ViettelPost
│
├── cli/                          # CLI commands
│   ├── sync.py                   # python -m app.cli.sync ...
│   └── seed_dia_danh.py          # python -m app.cli.seed_dia_danh
│
└── static/                       # Assets (logo, favicon)

alembic/                          # Migrations (DDL không phụ thuộc models — raw SQL trong 0001)
docker-compose.yml                # Postgres 16
```

### Luồng MVC chuẩn

1. **Request** → **Controller** (FastAPI route)
2. Controller gọi **Service** (business logic)
3. Service đọc/ghi **Model** (ORM) hoặc gọi **Integration** (VTP, Google Sheets)
4. Controller render **View** (Jinja2 template) hoặc trả JSON

Mỗi tầng có 1 trách nhiệm rõ ràng → dễ test, dễ thay thế từng phần.

## Các bảng DB

`du_lieu_sheet` (phẳng, mỗi row = 1 dòng sheet) → `phieu_giao_hang` → `hanh_trinh_pgh`. Cộng thêm: `tai_khoan_vtp`, `dia_danh_tinh/huyen/xa`, `log_dong_bo_sheet`, `log_api_vtp`, `cau_hinh`.

## Lệnh hữu ích

```powershell
# Xem log sync gần nhất
psql -h localhost -U postgres kinkin_pgh -c "SELECT ten_sheet, so_dong_doc, so_dong_them_moi, so_dong_cap_nhat, trang_thai FROM log_dong_bo_sheet ORDER BY id DESC LIMIT 10;"

# Đếm vận đơn Viettel chưa chốt
psql -h localhost -U postgres kinkin_pgh -c "SELECT COUNT(*) FROM du_lieu_sheet d WHERE d.phuong_thuc_gui ILIKE '%viettel%' AND NOT EXISTS (SELECT 1 FROM phieu_giao_hang p WHERE p.du_lieu_sheet_id = d.id AND p.ma_pgh_vtp IS NOT NULL);"

# Tắt Postgres
docker compose down
# Xoá data hoàn toàn
docker compose down -v
```
