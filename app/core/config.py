from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


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
    KK_USERNAME: str = ""
    KK_PASSWORD: str = ""
    KK_WAREHOUSE_IDS: str = ""
    KK_CUSTOMER_CODE: str = "450HN-GENKIN"
    KK_PACKAGEK_APIKEY: str = ""

    @property
    def kk_warehouse_ids(self) -> list[str]:
        return [s.strip() for s in self.KK_WAREHOUSE_IDS.split(",") if s.strip()]


settings = Settings()
