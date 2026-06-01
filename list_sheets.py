"""List all worksheets in the spreadsheet and identify ones in dd-mm-yy format."""
import re
import sys
import json
import gspread
from google.oauth2.service_account import Credentials

CREDS_FILE = r"c:\VScode\Kinkin - DF\BOT- DF.json"
SPREADSHEET_ID = "1S9FtklMhj6rKZmrtYx3jIKBz_xEDNrNYST0khlb1rB0"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]

# Match dd-mm-yy (allow dd-mm-yyyy too just in case)
DATE_RE = re.compile(r"^\d{1,2}-\d{1,2}-\d{2,4}$")


def main():
    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
    gc = gspread.authorize(creds)

    try:
        sh = gc.open_by_key(SPREADSHEET_ID)
    except gspread.exceptions.APIError as e:
        print("[ERROR] Cannot open spreadsheet:", e)
        sys.exit(1)

    print(f"Spreadsheet title: {sh.title}")
    print(f"Spreadsheet URL  : {sh.url}")
    print("-" * 60)

    worksheets = sh.worksheets()
    print(f"Total worksheets: {len(worksheets)}\n")

    date_sheets = []
    other_sheets = []
    for ws in worksheets:
        name = ws.title
        if DATE_RE.match(name.strip()):
            date_sheets.append(ws)
        else:
            other_sheets.append(ws)

    print(f"== Sheets in dd-mm-yy format ({len(date_sheets)}) ==")
    for ws in date_sheets:
        print(f"  - {ws.title}  (id={ws.id}, rows={ws.row_count}, cols={ws.col_count})")

    print(f"\n== Other sheets ({len(other_sheets)}) ==")
    for ws in other_sheets:
        print(f"  - {ws.title}  (id={ws.id}, rows={ws.row_count}, cols={ws.col_count})")

    # Persist mapping for next step
    out = {
        "spreadsheet_title": sh.title,
        "date_sheets": [ws.title for ws in date_sheets],
        "other_sheets": [ws.title for ws in other_sheets],
    }
    with open(r"c:\VScode\Kinkin - DF\sheets_index.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("\n[OK] Saved index -> sheets_index.json")


if __name__ == "__main__":
    main()
