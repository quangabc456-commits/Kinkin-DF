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
    if settings.CRON_WORKER_MIN_NGAY_CHOT:
        try:
            min_ngay = date.fromisoformat(settings.CRON_WORKER_MIN_NGAY_CHOT)
            cutoff = max(cutoff, min_ngay)
        except ValueError:
            pass
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


def _tao_phieu_cho_dien(
    session: Session, dong: DuLieuSheet, thieu: list[str]
) -> None:
    """Tạo row phieu_giao_hang với trang_thai_pgh='cho_dien_thong_tin' để UI hiển thị."""
    from sqlalchemy import select as _sel

    da_co = session.execute(
        _sel(PhieuGiaoHang).where(
            PhieuGiaoHang.du_lieu_sheet_id == dong.id,
            PhieuGiaoHang.trang_thai_pgh == "cho_dien_thong_tin",
        )
    ).scalar_one_or_none()
    if da_co is not None:
        da_co.thieu_truong_json = thieu
        return

    tk = session.execute(
        _sel(__import__("app.models", fromlist=["TaiKhoanVtp"]).TaiKhoanVtp).where(
            __import__("app.models", fromlist=["TaiKhoanVtp"]).TaiKhoanVtp.mac_dinh.is_(True)
        )
    ).scalar_one_or_none()
    if tk is None:
        return

    pgh = PhieuGiaoHang(
        du_lieu_sheet_id=dong.id,
        tai_khoan_vtp_id=tk.id,
        trang_thai_pgh="cho_dien_thong_tin",
        nguoi_nhan_ten=dong.ten_kh or "(chưa có)",
        nguoi_nhan_sdt=dong.sdt_nguoi_nhan or "(chưa có)",
        nguoi_nhan_dia_chi=dong.dia_chi_nguoi_nhan or "(chưa có)",
        hinh_thuc_tt=1,
        dich_vu_chinh="VCN",
        thieu_truong_json=thieu,
        chot_boi="cron_worker:check",
    )
    session.add(pgh)


def chay_tao_pgh(
    session: Session, batch: int, days_back: int, dry_run: bool
) -> dict[str, Any]:
    from app.services.chot_pgh import tao_pgh_tu_dong_sheet
    from app.services.kiem_tra_du_thong_tin import kiem_tra

    _log(f"tao_pgh: bắt đầu (batch={batch}, days_back={days_back}, dry_run={dry_run})")
    rows = _chon_dong_viettel_chua_chot(session, batch, days_back)
    _log(f"tao_pgh: tìm thấy {len(rows)} dòng chờ chốt")

    so_thanh_cong = 0
    so_thieu_tt = 0
    so_loi = 0
    lo_loi: list[dict] = []

    for r in rows:
        thieu = kiem_tra(r)
        if thieu:
            try:
                _tao_phieu_cho_dien(session, r, thieu)
                session.commit()
                so_thieu_tt += 1
            except Exception as e:
                session.rollback()
                so_loi += 1
                if len(lo_loi) < 5:
                    lo_loi.append(
                        {"id": r.id, "ma_van_don": r.ma_van_don, "loi": f"cho_dien: {e}"}
                    )
            continue

        if dry_run:
            so_thanh_cong += 1
            continue

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
        "status": "dry_run" if dry_run else "ok",
        "tim_thay": len(rows),
        "thanh_cong": so_thanh_cong,
        "thieu_thong_tin": so_thieu_tt,
        "loi": so_loi,
        "lo_loi": lo_loi,
    }
    _log(f"tao_pgh: kết thúc — {json.dumps(kq, ensure_ascii=False)}")
    return kq


def chay_tao_pgh_kinkin(
    session: Session, batch: int, dry_run: bool
) -> dict[str, Any]:
    """Phase 5 — tạo PGH kho đến trên Kinkin warehouse.

    HIỆN TẠI: stub, chỉ log số PGH đủ điều kiện. Khi nhận spec API → bổ sung
    service `tao_pgh_kinkin.tao_pgh_kho_den` và call ở đây.
    """
    from sqlalchemy import select as _sel

    rows = session.execute(
        _sel(PhieuGiaoHang)
        .where(
            PhieuGiaoHang.ma_pgh_vtp.is_not(None),
            PhieuGiaoHang.ma_pgh_kinkin.is_(None),
            PhieuGiaoHang.trang_thai_kinkin.in_(["chua_tao", "loi_api_kinkin"]),
        )
        .limit(batch)
    ).scalars().all()

    kq = {
        "status": "stub_cho_spec",
        "tim_thay": len(rows),
        "ghi_chu": "Chờ spec API Kinkin tạo PGH; phase này hiện chỉ đếm số đơn đủ điều kiện",
    }
    _log(f"tao_pgh_kinkin: {json.dumps(kq, ensure_ascii=False)}")
    return kq


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Cron worker Kinkin DF")
    parser.add_argument("--dry-run", action="store_true", help="Không call VTP")
    parser.add_argument("--skip-refresh", action="store_true")
    parser.add_argument("--skip-prefetch", action="store_true")
    parser.add_argument("--skip-create-pgh", action="store_true")
    parser.add_argument("--skip-kinkin", action="store_true", help="Skip phase tạo PGH Kinkin kho đến")
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

        if not args.skip_kinkin:
            try:
                chay_tao_pgh_kinkin(session, args.batch, dry_run)
            except Exception as e:
                _log(f"tao_pgh_kinkin: EXCEPTION {e!r}")
                session.rollback()

    _log("cron_worker end")
    return 0


if __name__ == "__main__":
    sys.exit(main())
