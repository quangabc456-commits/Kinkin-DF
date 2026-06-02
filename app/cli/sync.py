from __future__ import annotations

import argparse
import sys
from datetime import date

from app.services.sheet_sync import sync_all, sync_sheet


def _in_ket_qua(i: int, tong: int, r: dict) -> None:
    if "loi" in r:
        print(f"[{i}/{tong}] {r['ten_sheet']}: LỖI {r['loi']}")
    else:
        print(
            f"[{i}/{tong}] {r['ten_sheet']}: đọc={r['so_dong_doc']}, "
            f"thêm={r['so_them_moi']}, cập nhật={r['so_cap_nhat']}, lỗi={r['so_loi']}"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sync Google Sheet → DB")
    parser.add_argument("--sheet", help="Tên sheet đơn lẻ, vd: 25-05-26")
    parser.add_argument("--all", action="store_true", help="Sync mọi sheet dd-mm-yy")
    parser.add_argument("--from-date", help="Chỉ sync sheet >= ngày này (YYYY-MM-DD)")
    args = parser.parse_args(argv)

    if args.sheet:
        try:
            _in_ket_qua(1, 1, sync_sheet(args.sheet))
        except Exception as e:
            print(f"{args.sheet}: LỖI {e}")
        return 0

    if args.all:
        from_dt = date.fromisoformat(args.from_date) if args.from_date else None
        ket_qua = sync_all(from_dt)
        print(f"Sync {len(ket_qua)} sheet(s)...")
        for i, r in enumerate(ket_qua, 1):
            _in_ket_qua(i, len(ket_qua), r)
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
