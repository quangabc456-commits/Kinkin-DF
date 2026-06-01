from __future__ import annotations

import argparse
import sys
from datetime import date

from app.services.sheet_sync import list_date_sheets, parse_ngay_tu_ten_sheet, sync_sheet


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sync Google Sheet → DB")
    parser.add_argument("--sheet", help="Tên sheet đơn lẻ, vd: 25-05-26")
    parser.add_argument("--all", action="store_true", help="Sync mọi sheet dd-mm-yy")
    parser.add_argument("--from-date", help="Chỉ sync sheet >= ngày này (YYYY-MM-DD)")
    args = parser.parse_args(argv)

    targets: list[str] = []
    if args.sheet:
        targets = [args.sheet]
    elif args.all:
        targets = list_date_sheets()
        if args.from_date:
            from_dt = date.fromisoformat(args.from_date)
            targets = [t for t in targets if (parse_ngay_tu_ten_sheet(t) or date.min) >= from_dt]
    else:
        parser.print_help()
        return 1

    print(f"Sync {len(targets)} sheet(s)...")
    for i, t in enumerate(targets, 1):
        try:
            r = sync_sheet(t)
            print(
                f"[{i}/{len(targets)}] {t}: đọc={r['so_dong_doc']}, "
                f"thêm={r['so_them_moi']}, cập nhật={r['so_cap_nhat']}, lỗi={r['so_loi']}"
            )
        except Exception as e:
            print(f"[{i}/{len(targets)}] {t}: LỖI {e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
