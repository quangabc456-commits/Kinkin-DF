"""Read sample data from recent dd-mm-yy sheets to understand structure."""
import gspread
import json
from google.oauth2.service_account import Credentials

CREDS_FILE = r"c:\VScode\Kinkin - DF\BOT- DF.json"
SPREADSHEET_ID = "1S9FtklMhj6rKZmrtYx3jIKBz_xEDNrNYST0khlb1rB0"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]

# Pick a few representative sheets: most recent, mid-range, old
SAMPLE = ["25-05-26", "19-05-26", "18-05-26", "12-05-26", "30-04-26",
          "27-04-26", "20-04-26", "13-04-26"]


def main():
    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SPREADSHEET_ID)

    snapshots = {}
    for name in SAMPLE:
        try:
            ws = sh.worksheet(name)
        except gspread.exceptions.WorksheetNotFound:
            print(f"[skip] {name} not found")
            continue
        # Get first 12 rows, full width
        data = ws.get_values(f"A1:Z12")
        print("=" * 80)
        print(f"SHEET: {name}  (dims declared: {ws.row_count}x{ws.col_count})")
        print("-" * 80)
        for i, row in enumerate(data, 1):
            print(f"R{i:02d}: {row}")
        print()
        snapshots[name] = data

    with open(r"c:\VScode\Kinkin - DF\sample_snapshot.json", "w", encoding="utf-8") as f:
        json.dump(snapshots, f, ensure_ascii=False, indent=2)
    print("[OK] Wrote sample_snapshot.json")


if __name__ == "__main__":
    main()
