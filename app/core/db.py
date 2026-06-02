from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


# prepare_threshold=None: tắt prepared statement của psycopg3.
# Supabase transaction pooler (port 6543) ghép nhiều kết nối backend → prepared
# statement tạo ở connection này có thể không tồn tại ở connection khác, gây lỗi
# 'prepared statement "_pg3_x" does not exist'. Tắt đi để chạy ổn định qua pooler.
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    future=True,
    connect_args={"prepare_threshold": None},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


@contextmanager
def get_session() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
