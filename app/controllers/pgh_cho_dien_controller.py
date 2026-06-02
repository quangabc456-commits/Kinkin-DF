from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.templates import templates
from app.models import DuLieuSheet, PhieuGiaoHang
from app.services.kiem_tra_du_thong_tin import TRUONG_BAT_BUOC, kiem_tra, label_truong


router = APIRouter(prefix="/pgh/cho-dien-thong-tin", tags=["cho-dien"])


def _to_decimal(s: Optional[str]) -> Optional[Decimal]:
    if not s:
        return None
    s = s.strip().replace(",", ".")
    try:
        return Decimal(s)
    except (InvalidOperation, ValueError):
        return None


@router.get("/", response_class=HTMLResponse)
def trang_cho_dien(request: Request, session: Session = Depends(get_db)):
    """List các phieu_giao_hang đang chờ điền + dòng nguồn."""
    rows = (
        session.execute(
            select(PhieuGiaoHang, DuLieuSheet)
            .join(DuLieuSheet, PhieuGiaoHang.du_lieu_sheet_id == DuLieuSheet.id)
            .where(PhieuGiaoHang.trang_thai_pgh == "cho_dien_thong_tin")
            .order_by(PhieuGiaoHang.id.desc())
        )
        .all()
    )

    items = []
    for pgh, ds in rows:
        thieu_keys = pgh.thieu_truong_json or kiem_tra(ds)
        items.append(
            {
                "pgh_id": pgh.id,
                "du_lieu_sheet_id": ds.id,
                "ma_van_don": ds.ma_van_don,
                "ten_sheet": ds.ten_sheet,
                "ngay_chot": ds.ngay_chot,
                "ten_kh": ds.ten_kh or "",
                "sdt_nguoi_nhan": ds.sdt_nguoi_nhan or "",
                "dia_chi_nguoi_nhan": ds.dia_chi_nguoi_nhan or "",
                "nhom_san_pham": ds.nhom_san_pham or "",
                "can_nang_kg": str(ds.can_nang_kg) if ds.can_nang_kg is not None else "",
                "ghi_chu": ds.ghi_chu or "",
                "thieu_keys": thieu_keys,
                "thieu_labels": [label_truong(k) for k in thieu_keys],
            }
        )

    return templates.TemplateResponse(
        "pgh/cho_dien.html",
        {
            "request": request,
            "items": items,
            "truong_bat_buoc": TRUONG_BAT_BUOC,
        },
    )


@router.post("/{ds_id}/cap-nhat-thong-tin")
def cap_nhat_thong_tin(
    ds_id: int,
    ten_kh: str = Form(""),
    sdt_nguoi_nhan: str = Form(""),
    dia_chi_nguoi_nhan: str = Form(""),
    nhom_san_pham: str = Form(""),
    can_nang_kg: str = Form(""),
    ghi_chu: str = Form(""),
    session: Session = Depends(get_db),
):
    """Cập nhật du_lieu_sheet → xoá phieu_giao_hang đang chờ điền để worker tạo lại."""
    ds = session.get(DuLieuSheet, ds_id)
    if ds is None:
        raise HTTPException(404, f"Không tìm thấy dòng id={ds_id}")

    if ten_kh.strip():
        ds.ten_kh = ten_kh.strip()
    if sdt_nguoi_nhan.strip():
        ds.sdt_nguoi_nhan = sdt_nguoi_nhan.strip()
    if dia_chi_nguoi_nhan.strip():
        ds.dia_chi_nguoi_nhan = dia_chi_nguoi_nhan.strip()
    if nhom_san_pham.strip():
        ds.nhom_san_pham = nhom_san_pham.strip()
    can_nang_dec = _to_decimal(can_nang_kg)
    if can_nang_dec is not None:
        ds.can_nang_kg = can_nang_dec
    if ghi_chu.strip():
        ds.ghi_chu = ghi_chu.strip()

    session.execute(
        delete(PhieuGiaoHang).where(
            PhieuGiaoHang.du_lieu_sheet_id == ds_id,
            PhieuGiaoHang.trang_thai_pgh == "cho_dien_thong_tin",
        )
    )
    session.commit()
    return RedirectResponse(url="/pgh/cho-dien-thong-tin/", status_code=303)
