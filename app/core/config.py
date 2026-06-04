from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Thư mục gốc dự án (app/core/config.py -> ../../..)
PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/kinkin_pgh"

    GOOGLE_CREDS_PATH: str = "./BOT- DF.json"
    GOOGLE_CREDS_JSON_B64: str = ""
    SHEET_ID: str = "1S9FtklMhj6rKZmrtYx3jIKBz_xEDNrNYST0khlb1rB0"

    ENABLE_SYNC_UI: bool = True

    # Production VTP (tài khoản it.dept là tài khoản thật). Đổi về *dev nếu cần sandbox.
    VTP_BASE_URL: str = "https://partner.viettelpost.vn"
    VTP_PRINT_BASE_URL: str = "https://print.viettelpost.vn"
    # Tài khoản VTP (để seed vào bảng tai_khoan_vtp qua `python -m app.cli.seed_vtp`).
    # Secret — set trong .env, KHÔNG commit. Nơi dùng thật là bảng tai_khoan_vtp (đã mã hoá).
    VTP_SECRET_TOKEN: str = ""   # token LoginVTP (ưu tiên)
    VTP_USERNAME: str = ""       # fallback: username/password → Login → ownerconnect
    VTP_PASSWORD: str = ""

    FERNET_KEY: str = ""

    APP_HOST: str = "127.0.0.1"
    APP_PORT: int = 8000

    KK_BASE_IDENTITY: str = "https://identityapi.vanchuyenkinkin.com"
    KK_BASE_WAREHOUSE: str = "https://warehouseexportapi.vanchuyenkinkin.com"
    KK_BASE_DEPARTURE: str = "https://warehousedepartureapi.vanchuyenkinkin.com"
    # API kho đến — hệ THẬT *.vanchuyenkinkin.com (đã chuyển từ TEST *.dion.vn).
    # Path endpoint GIỐNG HỆT giữa 2 hệ → chỉ đổi host. (Test cũ: apikhoden/identity/apicore-kinkin.dion.vn.)
    KK_BASE_KHODEN: str = "https://warehouseexportapi.vanchuyenkinkin.com"   # PGH + địa chỉ + kiện F
    KK_BASE_KHODEN_IDENTITY: str = "https://identityapi.vanchuyenkinkin.com"  # /connect/token
    KK_BASE_KHODEN_CORE: str = "https://kinkincoreapi.vanchuyenkinkin.com"   # khách + địa danh
    # ID đối tác vận chuyển Viettel Post trên hệ kho đến (tạo PGH kho đến + VTP trong 1 call)
    VIETTELPOST_PARTNER_ID: int = 1002
    # Tài khoản kho đến hệ THẬT (CẦN cấp tài khoản vanchuyenkinkin.com có quyền WarehouseExport;
    # tài khoản nvadmin của dion.vn KHÔNG dùng được trên hệ thật)
    KK_KHODEN_USERNAME: str = ""
    KK_KHODEN_PASSWORD: str = ""
    KK_USERNAME: str = ""
    KK_PASSWORD: str = ""
    KK_WAREHOUSE_IDS: str = ""
    KK_CUSTOMER_CODE: str = "450HN-GENKIN"
    KK_PACKAGEK_APIKEY: str = ""
    KK_WEBHOOK_SECRET: str = ""

    CRON_WORKER_BATCH: int = 50
    CRON_WORKER_REFRESH_DAYS: int = 7
    CRON_WORKER_DRY_RUN: bool = False
    CRON_WORKER_MIN_NGAY_CHOT: str = "2026-01-01"  # chỉ xử lý phiếu có ngay_chot >= ngày này (rỗng = không filter)

    DEFAULT_KHO_DEN_ID: str = "5"
    MIN_DIA_CHI_LEN: int = 15

    @property
    def kk_warehouse_ids(self) -> list[str]:
        return [s.strip() for s in self.KK_WAREHOUSE_IDS.split(",") if s.strip()]

    @property
    def google_creds_abs_path(self) -> Path:
        """Đường dẫn tuyệt đối tới file creds — neo theo gốc dự án nếu là path tương đối,
        để app chạy từ thư mục làm việc nào cũng tìm thấy file."""
        p = Path(self.GOOGLE_CREDS_PATH)
        return p if p.is_absolute() else (PROJECT_ROOT / p)


settings = Settings()
