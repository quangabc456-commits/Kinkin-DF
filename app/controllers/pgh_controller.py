from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.templates import templates
from app.integrations.vtp_client import VtpError
from app.models import DuLieuSheet, PhieuGiaoHang, TaiKhoanVtp
from app.services.chot_pgh import tao_pgh_tu_dong_sheet


router = APIRouter()


def _query_van_don(session: Session, q: Optional[str], ngay: Optional[str]):
    stmt = select(DuLieuSheet).order_by(
        DuLieuSheet.ngay_chot.desc(), DuLieuSheet.sheet_row_index.asc()
    )
    conds = [DuLieuSheet.phuong_thuc_gui.ilike("%viettel%")]
    if q:
        like = f"%{q}%"
        conds.append(
            (DuLieuSheet.ten_kh.ilike(like))
            | (DuLieuSheet.ma_van_don.ilike(like))
            | (DuLieuSheet.ma_kien_k.ilike(like))
        )
    if ngay:
        conds.append(DuLieuSheet.ten_sheet == ngay)
    stmt = stmt.where(and_(*conds))
    return stmt


@router.get("/", response_class=HTMLResponse)
def trang_chu(
    request: Request,
    q: Optional[str] = None,
    ngay: Optional[str] = None,
    limit: int = 100,
    session: Session = Depends(get_db),
):
    stmt = _query_van_don(session, q, ngay).limit(limit)
    rows = session.execute(stmt).scalars().all()

    pgh_map: dict[int, PhieuGiaoHang] = {}
    if rows:
        ids = [r.id for r in rows]
        ds_pgh = (
            session.execute(
                select(PhieuGiaoHang).where(PhieuGiaoHang.du_lieu_sheet_id.in_(ids))
            )
            .scalars()
            .all()
        )
        for p in ds_pgh:
            existing = pgh_map.get(p.du_lieu_sheet_id)
            if existing is None or (p.ma_pgh_vtp and not existing.ma_pgh_vtp):
                pgh_map[p.du_lieu_sheet_id] = p

    days = session.execute(
        select(
            DuLieuSheet.ten_sheet,
            func.count().label("so_dong"),
            func.max(DuLieuSheet.ngay_chot).label("ng"),
        )
        .where(DuLieuSheet.phuong_thuc_gui.ilike("%viettel%"))
        .group_by(DuLieuSheet.ten_sheet)
        .order_by(func.max(DuLieuSheet.ngay_chot).desc())
        .limit(60)
    ).all()

    tai_khoans = (
        session.execute(select(TaiKhoanVtp).where(TaiKhoanVtp.kich_hoat.is_(True)))
        .scalars()
        .all()
    )

    return templates.TemplateResponse(
        "pgh/danh_sach.html",
        {
            "request": request,
            "rows": rows,
            "pgh_map": pgh_map,
            "q": q or "",
            "ngay": ngay or "",
            "days": days,
            "tai_khoans": tai_khoans,
        },
    )


@router.post("/chot/{du_lieu_sheet_id}")
def chot_pgh(
    du_lieu_sheet_id: int,
    tai_khoan_vtp_id: Optional[int] = Form(None),
    sender_fullname: str = Form(""),
    sender_phone: str = Form(""),
    sender_address: str = Form(""),
    session: Session = Depends(get_db),
):
    try:
        pgh = tao_pgh_tu_dong_sheet(
            session,
            du_lieu_sheet_id=du_lieu_sheet_id,
            tai_khoan_vtp_id=tai_khoan_vtp_id,
            sender_fullname=sender_fullname,
            sender_phone=sender_phone,
            sender_address=sender_address,
            user="ui",
        )
        session.commit()
    except (VtpError, ValueError) as e:
        session.commit()
        raise HTTPException(status_code=400, detail=str(e))
    return RedirectResponse(url=f"/pgh/{pgh.id}", status_code=303)


@router.get("/pgh/{pgh_id}", response_class=HTMLResponse)
def chi_tiet_pgh(pgh_id: int, request: Request, session: Session = Depends(get_db)):
    pgh = session.get(PhieuGiaoHang, pgh_id)
    if pgh is None:
        raise HTTPException(404, "Không tìm thấy PGH")
    dong = session.get(DuLieuSheet, pgh.du_lieu_sheet_id)
    return templates.TemplateResponse(
        "pgh/chi_tiet.html",
        {"request": request, "pgh": pgh, "dong": dong},
    )
