from __future__ import annotations

from typing import Optional
from urllib.parse import urlencode

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

PER_PAGE = 10


def _conds_van_don(q: Optional[str], ngay: Optional[str], pt: Optional[str]) -> list:
    """Điều kiện lọc vận đơn. `pt` = phương thức gửi (khớp chính xác); rỗng = mọi phương thức."""
    conds: list = []
    if pt:
        conds.append(DuLieuSheet.phuong_thuc_gui == pt)
    if q:
        like = f"%{q}%"
        conds.append(
            (DuLieuSheet.ten_kh.ilike(like))
            | (DuLieuSheet.ma_van_don.ilike(like))
            | (DuLieuSheet.ma_kien_k.ilike(like))
        )
    if ngay:
        conds.append(DuLieuSheet.ten_sheet == ngay)
    return conds


@router.get("/", response_class=HTMLResponse)
def trang_chu(
    request: Request,
    q: Optional[str] = None,
    ngay: Optional[str] = None,
    pt: Optional[str] = None,
    page: int = 1,
    session: Session = Depends(get_db),
):
    if page < 1:
        page = 1
    conds = _conds_van_don(q, ngay, pt)

    def _apply(stmt):
        return stmt.where(and_(*conds)) if conds else stmt

    total = session.execute(
        _apply(select(func.count()).select_from(DuLieuSheet))
    ).scalar() or 0
    total_pages = max(1, (total + PER_PAGE - 1) // PER_PAGE)
    if page > total_pages:
        page = total_pages

    offset = (page - 1) * PER_PAGE
    stmt = (
        _apply(select(DuLieuSheet))
        .order_by(DuLieuSheet.ngay_chot.desc(), DuLieuSheet.sheet_row_index.asc())
        .offset(offset)
        .limit(PER_PAGE)
    )
    rows = session.execute(stmt).scalars().all()

    base_params = {k: v for k, v in {"q": q, "ngay": ngay, "pt": pt}.items() if v}
    base_url = "/?" + (urlencode(base_params) + "&" if base_params else "")

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

    # Danh sách ngày chốt (theo phương thức đang lọc, nếu có)
    days_q = select(
        DuLieuSheet.ten_sheet,
        func.count().label("so_dong"),
        func.max(DuLieuSheet.ngay_chot).label("ng"),
    )
    if pt:
        days_q = days_q.where(DuLieuSheet.phuong_thuc_gui == pt)
    days = session.execute(
        days_q.group_by(DuLieuSheet.ten_sheet)
        .order_by(func.max(DuLieuSheet.ngay_chot).desc())
        .limit(60)
    ).all()

    # Danh sách phương thức gửi (để lọc theo từng loại) — kèm số dòng
    pt_rows = session.execute(
        select(DuLieuSheet.phuong_thuc_gui, func.count().label("n"))
        .group_by(DuLieuSheet.phuong_thuc_gui)
        .order_by(func.count().desc())
        .limit(60)
    ).all()
    phuong_thuc_list = [(p, n) for p, n in pt_rows if p]

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
            "pt": pt or "",
            "days": days,
            "phuong_thuc_list": phuong_thuc_list,
            "tai_khoans": tai_khoans,
            "page": page,
            "total_pages": total_pages,
            "total_items": total,
            "per_page": PER_PAGE,
            "base_url": base_url,
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
