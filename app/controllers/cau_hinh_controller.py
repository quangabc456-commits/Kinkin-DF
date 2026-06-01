from __future__ import annotations

import json
import re
import secrets
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.core.templates import templates
from app.integrations.kinkin_client import trang_thai_token as kinkin_trang_thai_token
from app.models import CauHinh, LogDongBoSheet
from app.services.apps_script import sinh_apps_script


router = APIRouter(prefix="/cau-hinh", tags=["cau-hinh"])

SHEET_ID_RE = re.compile(r"/spreadsheets/d/([a-zA-Z0-9_-]+)")


def _get_or_create(session: Session, khoa: str, default: str = "") -> CauHinh:
    row = session.execute(select(CauHinh).where(CauHinh.khoa == khoa)).scalar_one_or_none()
    if row is None:
        row = CauHinh(khoa=khoa, gia_tri=default)
        session.add(row)
        session.flush()
    return row


def _doc_bot_info() -> dict:
    try:
        if settings.GOOGLE_CREDS_JSON_B64:
            import base64

            raw = base64.b64decode(settings.GOOGLE_CREDS_JSON_B64).decode("utf-8")
            data = json.loads(raw)
        else:
            data = json.loads(Path(settings.GOOGLE_CREDS_PATH).read_text(encoding="utf-8"))
        return {
            "email": data.get("client_email"),
            "project": data.get("project_id"),
            "ok": True,
            "loi": None,
        }
    except Exception as e:
        return {"email": None, "project": None, "ok": False, "loi": str(e)}


def _bao_dam_webhook_secret(session: Session) -> str:
    row = _get_or_create(session, "WEBHOOK_SECRET", "")
    if not row.gia_tri:
        row.gia_tri = secrets.token_urlsafe(24)
        session.flush()
    return row.gia_tri


def _sync_all_bg() -> None:
    from app.services.sheet_sync import sync_all

    try:
        sync_all()
    except Exception as e:
        print(f"[sync_all] lỗi: {e}")


@router.get("/", response_class=HTMLResponse)
def trang_cau_hinh(request: Request, session: Session = Depends(get_db)):
    sheet_id_row = _get_or_create(session, "SHEET_ID", settings.SHEET_ID)
    webhook_base_row = _get_or_create(session, "WEBHOOK_BASE_URL", "")
    webhook_secret = _bao_dam_webhook_secret(session)
    session.commit()

    base_url = webhook_base_row.gia_tri or str(request.base_url).rstrip("/")
    webhook_url = f"{base_url}/webhook/sheet-changed"

    bot = _doc_bot_info()
    script = sinh_apps_script(webhook_url, webhook_secret)

    logs = (
        session.execute(select(LogDongBoSheet).order_by(LogDongBoSheet.id.desc()).limit(20))
        .scalars()
        .all()
    )

    sheet_url_hien_tai = (
        f"https://docs.google.com/spreadsheets/d/{sheet_id_row.gia_tri}/edit"
        if sheet_id_row.gia_tri
        else ""
    )

    kinkin_status = {
        "co_creds": bool(settings.KK_USERNAME and settings.KK_PASSWORD),
        "username": settings.KK_USERNAME or "",
        "warehouse_ids": settings.kk_warehouse_ids,
        "customer_code": settings.KK_CUSTOMER_CODE,
        "co_apikey_k": bool(settings.KK_PACKAGEK_APIKEY),
        "base_identity": settings.KK_BASE_IDENTITY,
        "base_warehouse": settings.KK_BASE_WAREHOUSE,
        **kinkin_trang_thai_token(),
    }

    return templates.TemplateResponse(
        "cau_hinh/index.html",
        {
            "request": request,
            "sheet_id": sheet_id_row.gia_tri or "",
            "sheet_url_hien_tai": sheet_url_hien_tai,
            "webhook_base_url": webhook_base_row.gia_tri or "",
            "webhook_url": webhook_url,
            "webhook_secret": webhook_secret,
            "bot": bot,
            "apps_script": script,
            "logs": logs,
            "kinkin_status": kinkin_status,
            "enable_sync_ui": settings.ENABLE_SYNC_UI,
        },
    )


@router.post("/sheet")
def cap_nhat_sheet(
    sheet_input: str = Form(""),
    webhook_base: str = Form(""),
    session: Session = Depends(get_db),
):
    sheet_input = (sheet_input or "").strip()
    if sheet_input:
        m = SHEET_ID_RE.search(sheet_input)
        sheet_id = m.group(1) if m else sheet_input
        row = _get_or_create(session, "SHEET_ID", "")
        row.gia_tri = sheet_id

    webhook_base = (webhook_base or "").strip().rstrip("/")
    if webhook_base:
        row = _get_or_create(session, "WEBHOOK_BASE_URL", "")
        row.gia_tri = webhook_base

    session.commit()
    return RedirectResponse(url="/cau-hinh/", status_code=303)


@router.post("/sync")
def kich_hoat_sync_toan_bo(background_tasks: BackgroundTasks):
    if not settings.ENABLE_SYNC_UI:
        from fastapi import HTTPException

        raise HTTPException(503, "Sync UI bị tắt trên môi trường này")
    background_tasks.add_task(_sync_all_bg)
    return RedirectResponse(url="/cau-hinh/?sync=queued", status_code=303)


@router.post("/rotate-secret")
def doi_secret(session: Session = Depends(get_db)):
    row = _get_or_create(session, "WEBHOOK_SECRET", "")
    row.gia_tri = secrets.token_urlsafe(24)
    session.commit()
    return RedirectResponse(url="/cau-hinh/", status_code=303)
