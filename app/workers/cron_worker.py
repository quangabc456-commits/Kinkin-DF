"""Cron worker chạy local qua PM2 mỗi 5 phút.

2 việc song song:
  1) Refresh status text từ Kinkin cho các dòng thiếu trang_thai_goc
  2) Tạo PGH ViettelPost cho các dòng phương thức = Viettel* chưa có PGH

Usage:
    .venv\\Scripts\\python.exe -m app.workers.cron_worker
    .venv\\Scripts\\python.exe -m app.workers.cron_worker --dry-run
    .venv\\Scripts\\python.exe -m app.workers.cron_worker --skip-refresh
    .venv\\Scripts\\python.exe -m app.workers.cron_worker --skip-create-pgh
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import date, datetime, timedelta, timezone
from typing import Any

from sqlalchemy import and_, not_, or_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_session
from app.models import DuLieuSheet, PhieuGiaoHang


def _log(msg: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def _chon_dong_viettel_chua_chot(
    session: Session, batch: int, days_back: int
) -> list[DuLieuSheet]:
    """Dòng phuong_thuc_gui ILIKE '%viettel%' và chưa có PGH ma_pgh_vtp."""
    cutoff = date.today() - timedelta(days=days_back)
    pgh_subq = (
        select(PhieuGiaoHang.du_lieu_sheet_id)
        .where(PhieuGiaoHang.ma_pgh_vtp.is_not(None))
        .subquery()
    )
    rows = session.execute(
        select(DuLieuSheet)
        .where(
            DuLieuSheet.ngay_chot >= cutoff,
            DuLieuSheet.phuong_thuc_gui.ilike("%viettel%"),
            DuLieuSheet.ma_van_don.is_not(None),
            not_(DuLieuSheet.id.in_(select(pgh_subq.c.du_lieu_sheet_id))),
        )
        .order_by(DuLieuSheet.ngay_chot.desc(), DuLieuSheet.id.desc())
        .limit(batch)
    ).scalars().all()
    return list(rows)


def chay_refresh(session: Session, batch: int, days_back: int) -> dict[str, Any]:
    from app.services.refresh_status_kinkin import refresh_status_batch

    _log(f"refresh_status: bắt đầu (batch={batch}, days_back={days_back})")
    t0 = time.time()
    kq = refresh_status_batch(session, batch=batch, days_back=days_back)
    kq["thoi_gian_s"] = round(time.time() - t0, 2)
    _log(f"refresh_status: kết thúc — {json.dumps(kq, ensure_ascii=False)}")
    return kq


def chay_prefetch_kinkin(
    session: Session, batch: int, days_back: int
) -> dict[str, Any]:
    from app.services.cache_kinkin import prefetch_batch

    _log(f"prefetch_kinkin: bắt đầu (batch={batch}, days_back={days_back})")
    t0 = time.time()
    kq = prefetch_batch(session, batch=batch, days_back=days_back)
    kq["thoi_gian_s"] = round(time.time() - t0, 2)
    _log(f"prefetch_kinkin: kết thúc — {json.dumps(kq, ensure_ascii=False)}")
    return kq


def chay_tao_pgh(
    session: Session, batch: int, days_back: int, dry_run: bool
) -> dict[str, Any]:
    from app.services.chot_pgh import tao_pgh_tu_dong_sheet

    _log(f"tao_pgh: bắt đầu (batch={batch}, days_back={days_back}, dry_run={dry_run})")
    rows = _chon_dong_viettel_chua_chot(session, batch, days_back)
    _log(f"tao_pgh: tìm thấy {len(rows)} dòng chờ chốt")

    if dry_run:
        return {
            "status": "dry_run",
            "tim_thay": len(rows),
            "mau_5_dong": [
                {"id": r.id, "ma_van_don": r.ma_van_don, "ten_kh": r.ten_kh}
                for r in rows[:5]
            ],
        }

    so_thanh_cong = 0
    so_loi = 0
    lo_loi: list[dict] = []

    for r in rows:
        try:
            tao_pgh_tu_dong_sheet(
                session,
                du_lieu_sheet_id=r.id,
                user="cron_worker",
            )
            session.commit()
            so_thanh_cong += 1
        except Exception as e:
            session.rollback()
            so_loi += 1
            if len(lo_loi) < 5:
                lo_loi.append({"id": r.id, "ma_van_don": r.ma_van_don, "loi": str(e)})
        time.sleep(0.5)

    kq = {
        "status": "ok",
        "tim_thay": len(rows),
        "thanh_cong": so_thanh_cong,
        "loi": so_loi,
        "lo_loi": lo_loi,
    }
    _log(f"tao_pgh: kết thúc — {json.dumps(kq, ensure_ascii=False)}")
    return kq


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Cron worker Kinkin DF")
    parser.add_argument("--dry-run", action="store_true", help="Không call VTP")
    parser.add_argument("--skip-refresh", action="store_true")
    parser.add_argument("--skip-prefetch", action="store_true")
    parser.add_argument("--skip-create-pgh", action="store_true")
    parser.add_argument(
        "--batch", type=int, default=settings.CRON_WORKER_BATCH, help="Số dòng mỗi vòng"
    )
    parser.add_argument(
        "--days-back",
        type=int,
        default=settings.CRON_WORKER_REFRESH_DAYS,
        help="Chỉ xét dòng có ngay_chot >= today - N ngày",
    )
    args = parser.parse_args(argv)

    dry_run = args.dry_run or settings.CRON_WORKER_DRY_RUN

    _log("=" * 60)
    _log(
        f"cron_worker start — dry_run={dry_run}, batch={args.batch}, "
        f"days_back={args.days_back}"
    )

    with get_session() as session:
        if not args.skip_refresh:
            try:
                chay_refresh(session, args.batch, args.days_back)
            except Exception as e:
                _log(f"refresh_status: EXCEPTION {e!r}")
                session.rollback()

        if not args.skip_prefetch:
            try:
                chay_prefetch_kinkin(session, args.batch, args.days_back)
            except Exception as e:
                _log(f"prefetch_kinkin: EXCEPTION {e!r}")
                session.rollback()

        if not args.skip_create_pgh:
            try:
                chay_tao_pgh(session, args.batch, args.days_back, dry_run)
            except Exception as e:
                _log(f"tao_pgh: EXCEPTION {e!r}")
                session.rollback()

    _log("cron_worker end")
    return 0


if __name__ == "__main__":
    sys.exit(main())
