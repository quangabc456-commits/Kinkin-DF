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

    VTP_BASE_URL: str = "https://partnerdev.viettelpost.vn"
    VTP_PRINT_BASE_URL: str = "https://dev-print.viettelpost.vn"

    FERNET_KEY: str = ""

    APP_HOST: str = "127.0.0.1"
    APP_PORT: int = 8000

    KK_BASE_IDENTITY: str = "https://identityapi.vanchuyenkinkin.com"
    KK_BASE_WAREHOUSE: str = "https://warehouseexportapi.vanchuyenkinkin.com"
    KK_BASE_DEPARTURE: str = "https://warehousedepartureapi.vanchuyenkinkin.com"
    # API kho đến — hệ *.dion.vn (RIÊNG, khác hệ vanchuyenkinkin.com ở trên)
    KK_BASE_KHODEN: str = "https://apikhoden-kinkin.dion.vn"      # PGH + địa chỉ
    KK_BASE_KHODEN_IDENTITY: str = "https://identity-kinkin.dion.vn"  # /connect/token
    KK_BASE_KHODEN_CORE: str = "https://apicore-kinkin.dion.vn"   # khách + địa danh
    # Tài khoản hệ dion.vn (KHÁC KK_USERNAME/KK_PASSWORD ở trên — aitool01 không dùng được)
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
