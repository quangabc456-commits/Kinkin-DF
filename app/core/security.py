from __future__ import annotations

from cryptography.fernet import Fernet

from app.core.config import settings


def _key() -> bytes:
    if not settings.FERNET_KEY:
        raise RuntimeError(
            "Chưa có FERNET_KEY trong .env. Tạo bằng: "
            "python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
        )
    return settings.FERNET_KEY.encode()


def ma_hoa(plain: str) -> str:
    return Fernet(_key()).encrypt(plain.encode()).decode()


def giai_ma(token: str) -> str:
    return Fernet(_key()).decrypt(token.encode()).decode()
