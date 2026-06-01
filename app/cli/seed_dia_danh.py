from __future__ import annotations

import sys

from app.services.seed_dia_danh import upsert_dia_danh


def main() -> int:
    r = upsert_dia_danh(verbose=True)
    print(f"\nHoàn tất: {r['tinh']} tỉnh, {r['huyen']} huyện, {r['xa']} xã/phường")
    return 0


if __name__ == "__main__":
    sys.exit(main())
