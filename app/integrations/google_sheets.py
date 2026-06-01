from __future__ import annotations

import base64
import json

import gspread
from google.oauth2.service_account import Credentials

from app.core.config import settings


SCOPES_READONLY = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]

SCOPES_RW = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def _doc_creds_info() -> dict:
    """Load service-account JSON từ env var (production) hoặc file (local)."""
    if settings.GOOGLE_CREDS_JSON_B64:
        raw = base64.b64decode(settings.GOOGLE_CREDS_JSON_B64).decode("utf-8")
        return json.loads(raw)
    with open(settings.GOOGLE_CREDS_PATH, encoding="utf-8") as f:
        return json.load(f)


def get_client(readonly: bool = True) -> gspread.Client:
    scopes = SCOPES_READONLY if readonly else SCOPES_RW
    creds = Credentials.from_service_account_info(_doc_creds_info(), scopes=scopes)
    return gspread.authorize(creds)
