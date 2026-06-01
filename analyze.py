"""Aggregate stats across all dd-mm-yy sheets:
   - distribution by year/month
   - totals (Tổng kiện, Tổng mã Tracking, Tổng cân) from header
   - compare oldest vs newest structure
"""
import re
import json
from collections import defaultdict, Counter
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

CREDS_FILE = r"c:\VScode\Kinkin - DF\BOT- DF.json"
SPREADSHEET_ID = "1S9FtklMhj6rKZmrtYx3jIKBz_xEDNrNYST0khlb1rB0"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]
DATE_RE = re.compile(r"^(\d{1,2})-(\d{1,2})-(\d{2,4})$")


def parse_num(s: str):
    """Vietnamese decimal uses comma. Convert to float."""
    if not s:
        return None
    s = s.strip().replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def parse_int(s: str):
    if not s:
        return None
    s = s.strip().replace(".", "").replace(",", "")
    try:
        return int(s)
    except ValueError:
        return None


def main():
    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SPREADSHEET_ID)

    # parse names
    parsed = []
    for ws in sh.worksheets():
        m = DATE_RE.match(ws.title.strip())
        if not m:
            continue
        dd, mm, yy = m.groups()
        try:
            d, mo, y = int(dd), int(mm), int(yy)
            if y < 100:
                y += 2000
            dt = datetime(y, mo, d)
            parsed.append((dt, ws))
        except ValueError:
            continue

    parsed.sort(key=lambda x: x[0])
    print(f"Total dd-mm-yy sheets parsed: {len(parsed)}")
    print(f"Earliest: {parsed[0][1].title}  ({parsed[0][0].date()})")
    print(f"Latest  : {parsed[-1][1].title}  ({parsed[-1][0].date()})")

    # Distribution by year
    by_year = Counter(dt.year for dt, _ in parsed)
    print("\n== Sheets by year ==")
    for y in sorted(by_year):
        print(f"  {y}: {by_year[y]} sheets")

    by_year_month = Counter((dt.year, dt.month) for dt, _ in parsed)
    print("\n== Sheets by year-month ==")
    for (y, m) in sorted(by_year_month):
        print(f"  {y}-{m:02d}: {by_year_month[(y, m)]}")

    # Batch read header info (A1:I6) for ALL dd-mm-yy sheets to harvest totals
    # gspread batch_get accepts list of ranges per sheet — but it is per spreadsheet,
    # so we use service.values_batch_get via gc.session — simpler: loop with batch sizes
    print("\n== Fetching header totals (Tổng kiện / Tổng tracking / Tổng cân) ==")
    totals = []
    # Build all ranges in one batch_get call (much faster than per-sheet)
    ranges = [f"'{ws.title}'!A1:I6" for _, ws in parsed]
    # gspread Spreadsheet.values_batch_get
    resp = sh.values_batch_get(ranges)
    value_ranges = resp.get("valueRanges", [])

    for (dt, ws), vr in zip(parsed, value_ranges):
        rows = vr.get("values", [])
        kien = trk = can = None
        invoice = None
        ngay_chot = None
        nv = None
        if len(rows) >= 2:
            r2 = rows[1] + [""] * 10
            invoice = r2[2] or None
            ngay_chot = r2[8] if len(r2) > 8 else None
        if len(rows) >= 4:
            r4 = rows[3] + [""] * 10
            nv = r4[2] or None
        if len(rows) >= 6:
            r6 = rows[5] + [""] * 10
            kien = parse_int(r6[2])
            trk = parse_int(r6[5])
            can = parse_num(r6[7])
        totals.append({
            "date": dt.date().isoformat(),
            "sheet": ws.title,
            "invoice": invoice,
            "ngay_chot": ngay_chot,
            "nhan_vien": nv,
            "tong_kien": kien,
            "tong_tracking": trk,
            "tong_can_kg": can,
        })

    # Save full
    with open(r"c:\VScode\Kinkin - DF\totals_per_day.json", "w", encoding="utf-8") as f:
        json.dump(totals, f, ensure_ascii=False, indent=2)

    # Aggregate per year
    print("\n== Aggregated totals per year ==")
    by_year_agg = defaultdict(lambda: {"days": 0, "kien": 0, "trk": 0, "can": 0.0,
                                        "missing": 0})
    for t in totals:
        y = int(t["date"][:4])
        ag = by_year_agg[y]
        ag["days"] += 1
        if t["tong_kien"]: ag["kien"] += t["tong_kien"]
        if t["tong_tracking"]: ag["trk"] += t["tong_tracking"]
        if t["tong_can_kg"]: ag["can"] += t["tong_can_kg"]
        if not t["tong_kien"] and not t["tong_tracking"]:
            ag["missing"] += 1

    print(f"{'Year':<6}{'Days':>6}{'Kien':>10}{'Tracking':>12}{'Can(kg)':>14}{'NoHdr':>8}")
    for y in sorted(by_year_agg):
        a = by_year_agg[y]
        print(f"{y:<6}{a['days']:>6}{a['kien']:>10}{a['trk']:>12}{a['can']:>14.2f}{a['missing']:>8}")

    # Employee counter
    nv_counter = Counter(t["nhan_vien"] for t in totals if t["nhan_vien"])
    print("\n== Nhân viên hỗ trợ (top) ==")
    for nv, c in nv_counter.most_common(10):
        print(f"  {nv}: {c} ngày")

    # Recent 15 days summary
    print("\n== Last 15 days (most recent) ==")
    for t in totals[-15:]:
        print(f"  {t['date']}  kien={t['tong_kien']}  trk={t['tong_tracking']}  can={t['tong_can_kg']}  nv={t['nhan_vien']}")

    print("\n[OK] Wrote totals_per_day.json")


if __name__ == "__main__":
    main()
