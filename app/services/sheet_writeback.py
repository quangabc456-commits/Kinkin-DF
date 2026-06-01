from __future__ import annotations

from app.integrations.google_sheets import get_client
from app.services.sheet_sync import get_current_sheet_id


def ghi_ma_pgh(ten_sheet: str, sheet_row_index: int, ma_pgh: str, cot: str = "M") -> None:
    """Ghi mã PGH vào ô cột `Trạng thái` (mặc định cột M) của 1 row trong sheet gốc."""
    gc = get_client(readonly=False)
    sh = gc.open_by_key(get_current_sheet_id())
    ws = sh.worksheet(ten_sheet)
    cell = f"{cot}{sheet_row_index}"
    ws.update(cell, [[ma_pgh]])
