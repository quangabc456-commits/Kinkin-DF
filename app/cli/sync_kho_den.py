from __future__ import annotations

import argparse
import sys

from app.core.db import SessionLocal
from app.services import kho_den_ref_sync as ref


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sync reference data hệ kho đến → DB (kd_*)")
    parser.add_argument("--all", action="store_true", help="Sync khách/địa chỉ/địa danh/kho")
    parser.add_argument("--deep", action="store_true", help="Kéo đủ Tỉnh→Huyện→Xã (nặng)")
    parser.add_argument("--kien-f", metavar="CUSTOMER_CODE", help="Sync kiện F của 1 khách")
    args = parser.parse_args(argv)

    session = SessionLocal()
    try:
        if args.kien_f:
            try:
                n = ref.sync_kien_f(session, args.kien_f)
                session.commit()
            except Exception as e:  # noqa: BLE001
                session.rollback()
                print(f"kd_kien_f [{args.kien_f}]: LỖI {e}")
                return 1
            print(f"kd_kien_f [{args.kien_f}]: {n} bản ghi")
            return 0
        if args.all:
            try:
                ket_qua = ref.sync_all(session, deep_dia_danh=args.deep)
            except Exception as e:  # noqa: BLE001
                session.rollback()
                print(f"sync_all: LỖI {e}")
                return 1
            for r in ket_qua:
                if r.get("ok"):
                    print(f"{r['bang']}: {r['so_doc']} bản ghi")
                else:
                    print(f"{r['bang']}: LỖI {r.get('loi')}")
            return 0
        parser.print_help()
        return 1
    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(main())
