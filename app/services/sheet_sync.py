from __future__ import annotations

import re
import time
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Optional

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.core.config import settings
from app.core.db import get_session
from app.integrations.google_sheets import get_client
from app.models import CauHinh, DuLieuSheet, LogDongBoSheet


DATE_RE = re.compile(r"^(\d{1,2})-(\d{1,2})-(\d{2,4})$")

DATA_START_ROW = 8
RANGE_READ = "A1:Q1000"


def get_current_sheet_id() -> str:
    """Đọc SHEET_ID từ cau_hinh (UI cấu hình), fallback về .env."""
    try:
        with get_session() as s:
            row = s.execute(select(CauHinh).where(CauHinh.khoa == "SHEET_ID")).scalar_one_or_none()
            if row and row.gia_tri:
                return row.gia_tri
    except Exception:
        pass
    return settings.SHEET_ID


def parse_so(s: Optional[str]) -> Optional[Decimal]:
    if s is None:
        return None
    s = s.strip()
    if not s:
        return None
    s = s.replace(".", "").replace(",", ".")
    try:
        return Decimal(s)
    except (InvalidOperation, ValueError):
        return None


def parse_ngay_tu_ten_sheet(name: str) -> Optional[date]:
    m = DATE_RE.match(name.strip())
    if not m:
        return None
    dd, mm, yy = m.groups()
    try:
        d = int(dd)
        mo = int(mm)
        y = int(yy)
        if y < 100:
            y += 2000
        return date(y, mo, d)
    except ValueError:
        return None


def parse_thong_tin_gui(raw: Optional[str]) -> tuple[Optional[str], Optional[str], Optional[str]]:
    if not raw:
        return (None, None, None)
    parts = [p.strip() for p in raw.split(";")]
    parts = [p for p in parts if p]
    nhom = parts[0] if len(parts) >= 1 else None
    dia_chi = parts[1] if len(parts) >= 2 else None
    sdt = parts[2] if len(parts) >= 3 else None
    return nhom, dia_chi, sdt


def parse_bool_match(s: Optional[str]) -> Optional[bool]:
    if not s:
        return None
    s = s.strip().upper()
    if s == "TRUE":
        return True
    if s == "FALSE":
        return False
    return None


def _get(row: list[str], idx: int) -> str:
    if idx >= len(row):
        return ""
    return (row[idx] or "").strip()


def map_row(
    ten_sheet: str,
    ngay_chot: date,
    sheet_row_index: int,
    row: list[str],
    carry: dict,
) -> Optional[dict]:
    """Map 1 sheet row (after header) → dict insertable. Updates `carry` for fill-forward."""

    ma_kien_k = _get(row, 1) or carry.get("ma_kien_k")
    can_nang_kien = parse_so(_get(row, 2)) if _get(row, 2) else carry.get("can_nang_kien_kg")
    ma_f_cha = _get(row, 3) or carry.get("ma_f_cha")
    ma_thung = _get(row, 4) or None
    ma_van_don = _get(row, 5)

    carry["ma_kien_k"] = ma_kien_k
    carry["can_nang_kien_kg"] = can_nang_kien
    carry["ma_f_cha"] = ma_f_cha

    if not ma_van_don:
        return None

    thong_tin_raw = _get(row, 11)
    nhom_sp, dc_nguoi_nhan, sdt = parse_thong_tin_gui(thong_tin_raw)

    return {
        "ten_sheet": ten_sheet,
        "ngay_chot": ngay_chot,
        "sheet_row_index": sheet_row_index,
        "ma_kien_k": ma_kien_k,
        "can_nang_kien_kg": can_nang_kien,
        "ma_f_cha": ma_f_cha,
        "ma_thung": ma_thung,
        "ma_van_don": ma_van_don,
        "can_nang_kg": parse_so(_get(row, 6)),
        "phu_thu": _get(row, 7) or None,
        "ghi_chu": _get(row, 8) or None,
        "ten_kh": _get(row, 9) or None,
        "phuong_thuc_gui": _get(row, 10) or None,
        "thong_tin_gui_raw": thong_tin_raw or None,
        "nhom_san_pham": nhom_sp,
        "dia_chi_nguoi_nhan": dc_nguoi_nhan,
        "sdt_nguoi_nhan": sdt,
        "trang_thai_goc": _get(row, 12) or None,
        "ma_genkin": _get(row, 14) or None,
        "khoi_luong_genkin_kg": parse_so(_get(row, 15)),
        "co_match_genkin": parse_bool_match(_get(row, 16)),
        "dong_bo_lan_cuoi_luc": datetime.now(timezone.utc),
    }


def sync_sheet(ten_sheet: str) -> dict:
    ngay = parse_ngay_tu_ten_sheet(ten_sheet)
    if ngay is None:
        raise ValueError(f"Tên sheet không đúng định dạng dd-mm-yy: {ten_sheet}")

    gc = get_client(readonly=True)
    sh = gc.open_by_key(get_current_sheet_id())
    ws = sh.worksheet(ten_sheet)
    values = ws.get_values(RANGE_READ)

    rows_payload: list[dict] = []
    carry: dict = {"ma_kien_k": None, "can_nang_kien_kg": None, "ma_f_cha": None}
    so_dong_loi = 0
    chi_tiet_loi: list[dict] = []

    for i, row in enumerate(values, start=1):
        if i < DATA_START_ROW:
            continue
        try:
            payload = map_row(ten_sheet, ngay, i, row, carry)
            if payload:
                rows_payload.append(payload)
        except Exception as e:
            so_dong_loi += 1
            chi_tiet_loi.append({"row": i, "loi": str(e), "raw": row[:6]})

    so_dong_doc = len(rows_payload)
    so_them_moi = 0
    so_cap_nhat = 0

    bat_dau = datetime.now(timezone.utc)
    with get_session() as session:
        log = LogDongBoSheet(
            ten_sheet=ten_sheet,
            bat_dau_luc=bat_dau,
            so_dong_doc=so_dong_doc,
            trang_thai="dang_chay",
        )
        session.add(log)
        session.flush()

        for payload in rows_payload:
            exists = session.execute(
                select(DuLieuSheet.id).where(
                    DuLieuSheet.ten_sheet == payload["ten_sheet"],
                    DuLieuSheet.sheet_row_index == payload["sheet_row_index"],
                )
            ).first()

            stmt = pg_insert(DuLieuSheet).values(**payload)
            stmt = stmt.on_conflict_do_update(
                index_elements=["ten_sheet", "sheet_row_index"],
                set_={
                    k: v
                    for k, v in payload.items()
                    if k not in ("ten_sheet", "sheet_row_index")
                },
            )
            session.execute(stmt)
            if exists:
                so_cap_nhat += 1
            else:
                so_them_moi += 1

        log.so_dong_them_moi = so_them_moi
        log.so_dong_cap_nhat = so_cap_nhat
        log.so_dong_loi = so_dong_loi
        log.chi_tiet_loi = chi_tiet_loi or None
        log.ket_thuc_luc = datetime.now(timezone.utc)
        log.trang_thai = "thanh_cong" if so_dong_loi == 0 else "loi"

    return {
        "ten_sheet": ten_sheet,
        "so_dong_doc": so_dong_doc,
        "so_them_moi": so_them_moi,
        "so_cap_nhat": so_cap_nhat,
        "so_loi": so_dong_loi,
    }


def list_date_sheets() -> list[str]:
    gc = get_client(readonly=True)
    sh = gc.open_by_key(get_current_sheet_id())
    out = []
    for ws in sh.worksheets():
        if parse_ngay_tu_ten_sheet(ws.title) is not None:
            out.append(ws.title)
    return out


def sync_all(from_date: Optional[date] = None) -> list[dict]:
    targets = list_date_sheets()
    if from_date:
        targets = [t for t in targets if (parse_ngay_tu_ten_sheet(t) or date.min) >= from_date]

    ket_qua: list[dict] = []
    for t in targets:
        try:
            ket_qua.append(sync_sheet(t))
        except Exception as e:
            ket_qua.append({"ten_sheet": t, "loi": str(e)})
        time.sleep(0.3)
    return ket_qua
