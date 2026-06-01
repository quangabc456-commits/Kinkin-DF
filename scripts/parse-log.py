import json
import re

path = r"C:\Users\KK_IT_02\.claude\projects\c--VScode-Kinkin---DF\b03d5cb3-5360-4fa2-a001-af13e917a4f0\tool-results\bk4mvx7hj.txt"
with open(path, encoding="utf-8") as f:
    text = f.read()

for match in re.finditer(r'\{"id":[^\n]+\}', text):
    raw = match.group(0)
    try:
        obj = json.loads(raw)
    except Exception:
        continue
    msg = obj.get("message", "")
    if "OperationalError" in msg or "connection failed" in msg:
        print("=" * 70)
        for line in msg.split("\n"):
            if any(
                kw in line
                for kw in (
                    "OperationalError",
                    "connection failed",
                    "connection to server",
                    "Tenant",
                    "tenant",
                    "FATAL",
                    "host",
                    "authentication",
                )
            ):
                print(line.strip())
        break
