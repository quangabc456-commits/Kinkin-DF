"""Seed/cập nhật 1 tài khoản VTP vào bảng tai_khoan_vtp từ .env.

Đọc VTP_USERNAME / VTP_PASSWORD / VTP_SECRET_TOKEN (config) → upsert theo username,
mã hoá password bằng Fernet (cần FERNET_KEY). Dùng:
    python -m app.cli.seed_vtp
(VtpClient ưu tiên secret_token (LoginVTP), fallback username/password.)
"""
from __future__ import annotations

import argparse
import sys

from sqlalchemy import select

from app.core.config import settings
from app.core.db import SessionLocal
from app.core.security import ma_hoa
from app.models import TaiKhoanVtp


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Seed tài khoản VTP vào DB từ .env")
    parser.add_argument("--ten", default="it.dept (Kinkin)", help="Tên hiển thị")
    parser.add_argument(
        "--moi-truong", default="production", choices=["production", "development"]
    )
    args = parser.parse_args(argv)

    username = settings.VTP_USERNAME.strip()
    password = settings.VTP_PASSWORD.strip()
    token = settings.VTP_SECRET_TOKEN.strip()
    if not username:
        print("Thiếu VTP_USERNAME trong .env")
        return 1
    if not password and not token:
        print("Cần VTP_PASSWORD hoặc VTP_SECRET_TOKEN trong .env")
        return 1
    if password and not settings.FERNET_KEY:
        print("Thiếu FERNET_KEY để mã hoá password")
        return 1

    session = SessionLocal()
    try:
        tk = session.execute(
            select(TaiKhoanVtp).where(TaiKhoanVtp.username == username)
        ).scalar_one_or_none()
        hanh_dong = "Cập nhật" if tk else "Tạo mới"
        if tk is None:
            tk = TaiKhoanVtp(
                ten_hien_thi=args.ten, username=username,
                kich_hoat=True, moi_truong=args.moi_truong,
            )
            session.add(tk)
        else:
            tk.ten_hien_thi = args.ten or tk.ten_hien_thi
            tk.moi_truong = args.moi_truong
            tk.kich_hoat = True

        if password:
            try:
                tk.password_enc = ma_hoa(password)
            except Exception as e:  # noqa: BLE001 — FERNET_KEY hỏng: bỏ qua password nếu có token
                if not token:
                    raise
                print(
                    f"  CẢNH BÁO: không mã hoá được password ({e}). Bỏ qua password, "
                    "dùng secret_token. Sửa FERNET_KEY hợp lệ rồi seed lại để lưu password."
                )
        if token:
            tk.secret_token = token
        tk.token_hien_tai = None  # reset cache → login lại
        tk.token_het_han_luc = None
        session.flush()

        # Đặt mặc định nếu chưa có default (hoặc default đang là chính nó)
        co_mac_dinh = session.execute(
            select(TaiKhoanVtp).where(TaiKhoanVtp.mac_dinh.is_(True))
        ).scalar_one_or_none()
        if co_mac_dinh is None or co_mac_dinh.username == username:
            for r in session.execute(select(TaiKhoanVtp)).scalars():
                r.mac_dinh = False
            tk.mac_dinh = True

        session.commit()
        print(
            f"{hanh_dong} VTP: {username} | mặc định={tk.mac_dinh} "
            f"| có_token={bool(tk.secret_token)} | có_password={bool(tk.password_enc)} "
            f"| môi_trường={tk.moi_truong}"
        )
        return 0
    except Exception as e:  # noqa: BLE001
        session.rollback()
        print(f"LỖI seed VTP: {e}")
        return 1
    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(main())
