from __future__ import annotations

import json
import re
import secrets

from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.core.security import ma_hoa
from app.core.templates import templates
from app.integrations.kinkin_client import trang_thai_token as kinkin_trang_thai_token
from app.models import CauHinh, LogDongBoSheet, TaiKhoanVtp
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
            data = json.loads(settings.google_creds_abs_path.read_text(encoding="utf-8"))
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


def _liet_ke_tai_khoan_vtp(session: Session) -> list[dict]:
    rows = (
        session.execute(select(TaiKhoanVtp).order_by(TaiKhoanVtp.id))
        .scalars()
        .all()
    )
    return [
        {
            "id": r.id,
            "ten_hien_thi": r.ten_hien_thi,
            "username": r.username,
            "co_password": bool(r.password_enc),
            "co_secret_token": bool(r.secret_token),
            "co_token": bool(r.token_hien_tai),
            "token_het_han_luc": r.token_het_han_luc.isoformat() if r.token_het_han_luc else None,
            "mac_dinh": r.mac_dinh,
            "kich_hoat": r.kich_hoat,
            "moi_truong": r.moi_truong,
        }
        for r in rows
    ]


@router.get("/", response_class=HTMLResponse)
def trang_cau_hinh(request: Request, session: Session = Depends(get_db)):
    sheet_id_row = _get_or_create(session, "SHEET_ID", settings.SHEET_ID)
    webhook_secret = _bao_dam_webhook_secret(session)
    session.commit()

    base_url = str(request.base_url).rstrip("/")
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
            "webhook_url": webhook_url,
            "webhook_secret": webhook_secret,
            "bot": bot,
            "apps_script": script,
            "logs": logs,
            "kinkin_status": kinkin_status,
            "enable_sync_ui": settings.ENABLE_SYNC_UI,
            "vtp_accounts": _liet_ke_tai_khoan_vtp(session),
            "co_fernet": bool(settings.FERNET_KEY),
        },
    )


@router.post("/sheet")
def cap_nhat_sheet(
    sheet_input: str = Form(""),
    session: Session = Depends(get_db),
):
    sheet_input = (sheet_input or "").strip()
    if sheet_input:
        m = SHEET_ID_RE.search(sheet_input)
        sheet_id = m.group(1) if m else sheet_input
        row = _get_or_create(session, "SHEET_ID", "")
        row.gia_tri = sheet_id

    session.commit()
    return RedirectResponse(url="/cau-hinh/", status_code=303)


@router.post("/sync")
def kich_hoat_sync_toan_bo(background_tasks: BackgroundTasks):
    if not settings.ENABLE_SYNC_UI:
        raise HTTPException(503, "Sync UI bị tắt trên môi trường này")
    background_tasks.add_task(_sync_all_bg)
    return RedirectResponse(url="/cau-hinh/?sync=queued", status_code=303)


@router.post("/rotate-secret")
def doi_secret(session: Session = Depends(get_db)):
    row = _get_or_create(session, "WEBHOOK_SECRET", "")
    row.gia_tri = secrets.token_urlsafe(24)
    session.commit()
    return RedirectResponse(url="/cau-hinh/", status_code=303)


# ───────────────── Tài khoản ViettelPost CRUD ─────────────────

@router.post("/tai-khoan-vtp/them")
def them_tai_khoan_vtp(
    ten_hien_thi: str = Form(...),
    username: str = Form(...),
    password: str = Form(""),
    secret_token: str = Form(""),
    webhook_secret: str = Form(""),
    moi_truong: str = Form("production"),
    mac_dinh: str = Form(""),
    session: Session = Depends(get_db),
):
    ten_hien_thi = ten_hien_thi.strip()
    username = username.strip()
    password = password.strip()
    secret_token = secret_token.strip()
    webhook_secret = webhook_secret.strip()

    if not ten_hien_thi or not username:
        raise HTTPException(400, "Tên hiển thị và Username bắt buộc")
    if not password and not secret_token:
        raise HTTPException(400, "Phải nhập Password HOẶC Secret token")
    if password and not settings.FERNET_KEY:
        raise HTTPException(503, "Thiếu FERNET_KEY trong .env để mã hoá password")

    da_co = session.execute(
        select(TaiKhoanVtp).where(TaiKhoanVtp.username == username)
    ).scalar_one_or_none()
    if da_co is not None:
        raise HTTPException(400, f"Username '{username}' đã tồn tại (id={da_co.id})")

    la_mac_dinh = mac_dinh in ("on", "true", "1", "yes")
    if la_mac_dinh:
        for r in session.execute(select(TaiKhoanVtp)).scalars():
            r.mac_dinh = False
    else:
        co_mac_dinh = session.execute(
            select(TaiKhoanVtp).where(TaiKhoanVtp.mac_dinh.is_(True))
        ).scalar_one_or_none()
        if co_mac_dinh is None:
            la_mac_dinh = True

    tk = TaiKhoanVtp(
        ten_hien_thi=ten_hien_thi,
        username=username,
        password_enc=ma_hoa(password) if password else None,
        secret_token=secret_token or None,
        webhook_secret=webhook_secret or None,
        mac_dinh=la_mac_dinh,
        kich_hoat=True,
        moi_truong=moi_truong if moi_truong in ("production", "development") else "production",
    )
    session.add(tk)
    session.commit()
    return RedirectResponse(url="/cau-hinh/#vtp-accounts", status_code=303)


@router.post("/tai-khoan-vtp/{tk_id}/cap-nhat")
def cap_nhat_tai_khoan_vtp(
    tk_id: int,
    ten_hien_thi: str = Form(...),
    password: str = Form(""),
    secret_token: str = Form(""),
    webhook_secret: str = Form(""),
    moi_truong: str = Form("production"),
    kich_hoat: str = Form(""),
    session: Session = Depends(get_db),
):
    tk = session.get(TaiKhoanVtp, tk_id)
    if tk is None:
        raise HTTPException(404, f"Không tìm thấy tài khoản id={tk_id}")

    tk.ten_hien_thi = ten_hien_thi.strip() or tk.ten_hien_thi
    if password.strip():
        if not settings.FERNET_KEY:
            raise HTTPException(503, "Thiếu FERNET_KEY để mã hoá password mới")
        tk.password_enc = ma_hoa(password.strip())
        tk.token_hien_tai = None
        tk.token_het_han_luc = None
    if secret_token.strip():
        tk.secret_token = secret_token.strip()
        tk.token_hien_tai = None
        tk.token_het_han_luc = None
    if webhook_secret.strip():
        tk.webhook_secret = webhook_secret.strip()
    if moi_truong in ("production", "development"):
        tk.moi_truong = moi_truong
    tk.kich_hoat = kich_hoat in ("on", "true", "1", "yes")

    session.commit()
    return RedirectResponse(url="/cau-hinh/#vtp-accounts", status_code=303)


@router.post("/tai-khoan-vtp/{tk_id}/dat-mac-dinh")
def dat_mac_dinh_vtp(tk_id: int, session: Session = Depends(get_db)):
    tk = session.get(TaiKhoanVtp, tk_id)
    if tk is None:
        raise HTTPException(404, f"Không tìm thấy tài khoản id={tk_id}")
    for r in session.execute(select(TaiKhoanVtp)).scalars():
        r.mac_dinh = False
    tk.mac_dinh = True
    tk.kich_hoat = True
    session.commit()
    return RedirectResponse(url="/cau-hinh/#vtp-accounts", status_code=303)


@router.post("/tai-khoan-vtp/{tk_id}/xoa")
def xoa_tai_khoan_vtp(tk_id: int, session: Session = Depends(get_db)):
    tk = session.get(TaiKhoanVtp, tk_id)
    if tk is None:
        raise HTTPException(404, f"Không tìm thấy tài khoản id={tk_id}")
    from app.models import PhieuGiaoHang

    so_pgh = session.execute(
        select(PhieuGiaoHang).where(PhieuGiaoHang.tai_khoan_vtp_id == tk_id).limit(1)
    ).scalar_one_or_none()
    if so_pgh is not None:
        raise HTTPException(
            400,
            f"Tài khoản đã được dùng để chốt PGH (vd id={so_pgh.id}). "
            "Tắt 'Kích hoạt' thay vì xoá.",
        )
    session.delete(tk)
    session.commit()
    return RedirectResponse(url="/cau-hinh/#vtp-accounts", status_code=303)
