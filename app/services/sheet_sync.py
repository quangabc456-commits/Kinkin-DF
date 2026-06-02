from __future__ import annotations

import re
import time
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Optional

from gspread.exceptions import APIError
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.core.config import settings
from app.core.db import get_session
from app.integrations.google_sheets import get_client
from app.models import CauHinh, DuLieuSheet, LogDongBoSheet


DATE_RE = re.compile(r"^(\d{1,2})-(\d{1,2})-(\d{2,4})$")

DATA_START_ROW = 8
RANGE_READ = "A1:Q1000"

# Mã lỗi Google coi là tạm thời → retry với backoff (429 = vượt hạn mức request).
_RETRY_CODES = {429, 500, 502, 503}


def _api_retry(fn, *args, lan: int = 6, cho_ban_dau: float = 5.0, **kwargs):
    """Gọi 1 hàm gspread, tự retry + exponential backoff khi gặp rate-limit/lỗi tạm thời."""
    delay = cho_ban_dau
    for attempt in range(1, lan + 1):
        try:
            return fn(*args, **kwargs)
        except APIError as e:
            code = getattr(getattr(e, "response", None), "status_code", None)
            if code in _RETRY_CODES and attempt < lan:
                time.sleep(delay)
                delay = min(delay * 2, 60.0)
                continue
            raise
    raise RuntimeError("không thể tới đây")  # giúp type-checker hiểu hàm luôn return hoặc raise


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


# Nhãn cột "mã vận đơn" — dùng để nhận diện dòng tiêu đề lọt vào vùng dữ liệu
# (vài sheet cũ đặt header ở row 8 thay vì rows 1-7).
_HEADER_MA_VAN_DON = {"mã vận đơn", "ma van don", "mã vđ"}


def _la_dong_header(row: list[str]) -> bool:
    return _get(row, 5).lower() in _HEADER_MA_VAN_DON


def map_row(
    ten_sheet: str,
    ngay_chot: date,
    sheet_row_index: int,
    row: list[str],
    carry: dict,
) -> Optional[dict]:
    """Map 1 sheet row (after header) → dict insertable. Updates `carry` for fill-forward."""

    # Vài sheet cũ để dòng tiêu đề ở row 8 (vùng dữ liệu) → bỏ qua, tránh nhét
    # "Mã Vận đơn"... vào DB và đụng ràng buộc unique ma_van_don.
    if _la_dong_header(row):
        return None

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


def sync_sheet(ten_sheet: str, ws=None) -> dict:
    """Sync 1 sheet. Truyền sẵn `ws` (worksheet đã mở) để tránh mở lại spreadsheet
    mỗi lần — quan trọng khi sync_all chạy hàng trăm sheet (né rate-limit Google)."""
    ngay = parse_ngay_tu_ten_sheet(ten_sheet)
    if ngay is None:
        raise ValueError(f"Tên sheet không đúng định dạng dd-mm-yy: {ten_sheet}")

    if ws is None:
        gc = get_client(readonly=True)
        sh = _api_retry(gc.open_by_key, get_current_sheet_id())
        ws = sh.worksheet(ten_sheet)
    values = _api_retry(ws.get_values, RANGE_READ)

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

        if rows_payload:
            # Lấy 1 lần các row_index đã có của sheet này → đếm thêm/cập nhật trong RAM,
            # tránh 1 query SELECT mỗi dòng (quan trọng khi ghi qua pooler Supabase từ xa).
            existing_idx = set(
                session.execute(
                    select(DuLieuSheet.sheet_row_index).where(
                        DuLieuSheet.ten_sheet == ten_sheet
                    )
                ).scalars().all()
            )
            so_cap_nhat = sum(1 for p in rows_payload if p["sheet_row_index"] in existing_idx)
            so_them_moi = len(rows_payload) - so_cap_nhat

            # Upsert cả sheet trong 1 lệnh (thay vì mỗi dòng 1 lệnh).
            cap_nhat_cols = [
                k for k in rows_payload[0] if k not in ("ten_sheet", "sheet_row_index")
            ]
            ins = pg_insert(DuLieuSheet).values(rows_payload)
            stmt = ins.on_conflict_do_update(
                index_elements=["ten_sheet", "sheet_row_index"],
                set_={k: getattr(ins.excluded, k) for k in cap_nhat_cols},
            )
            session.execute(stmt)

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
    """Sync mọi sheet dd-mm-yy. Mở spreadsheet + lấy danh sách worksheet 1 LẦN
    rồi tái dùng cho từng sheet → tránh gọi open_by_key lặp lại (nguyên nhân chính
    gây rate-limit 429 khiến sync_all chạy không ổn định)."""
    gc = get_client(readonly=True)
    sh = _api_retry(gc.open_by_key, get_current_sheet_id())
    ws_map = {ws.title: ws for ws in _api_retry(sh.worksheets)}

    targets = [t for t in ws_map if parse_ngay_tu_ten_sheet(t) is not None]
    if from_date:
        targets = [t for t in targets if (parse_ngay_tu_ten_sheet(t) or date.min) >= from_date]
    # Xử lý theo thứ tự ngày mới → cũ để sheet gần đây vào DB trước.
    targets.sort(key=lambda t: parse_ngay_tu_ten_sheet(t) or date.min, reverse=True)

    ket_qua: list[dict] = []
    for t in targets:
        try:
            ket_qua.append(sync_sheet(t, ws=ws_map[t]))
        except Exception as e:
            ket_qua.append({"ten_sheet": t, "loi": str(e)})
        time.sleep(0.3)
    return ket_qua
