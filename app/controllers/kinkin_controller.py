from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models import CacheKinkinMa, DuLieuSheet
from app.services.cache_kinkin import doc_cache, prefetch_code
from app.services.kinkin_lookup import loai_ma


router = APIRouter(prefix="/api/kinkin", tags=["kinkin"])


def _dong_sheet_theo_code(session: Session, code: str) -> DuLieuSheet | None:
    for col in (
        DuLieuSheet.ma_van_don,
        DuLieuSheet.ma_thung,
        DuLieuSheet.ma_f_cha,
        DuLieuSheet.ma_kien_k,
    ):
        dong = session.execute(
            select(DuLieuSheet)
            .where(col == code)
            .order_by(DuLieuSheet.id.desc())
            .limit(1)
        ).scalars().first()
        if dong is not None:
            return dong
    return None


def _local_to_dict(dong: DuLieuSheet) -> dict:
    return {
        "ten_sheet": dong.ten_sheet,
        "ngay_chot": dong.ngay_chot.isoformat() if dong.ngay_chot else None,
        "ma_kien_k": dong.ma_kien_k,
        "ma_f_cha": dong.ma_f_cha,
        "ma_thung": dong.ma_thung,
        "ma_van_don": dong.ma_van_don,
        "ten_kh": dong.ten_kh,
        "sdt_nguoi_nhan": dong.sdt_nguoi_nhan,
        "dia_chi_nguoi_nhan": dong.dia_chi_nguoi_nhan,
        "phuong_thuc_gui": dong.phuong_thuc_gui,
        "nhom_san_pham": dong.nhom_san_pham,
        "can_nang_kg": float(dong.can_nang_kg) if dong.can_nang_kg else None,
        "ghi_chu": dong.ghi_chu,
        "trang_thai_goc": dong.trang_thai_goc,
    }


def _cache_to_dict(c: CacheKinkinMa) -> dict:
    return {
        "ma_don_chinh": c.ma_don_chinh,
        "bill_code": c.bill_code,
        "trang_thai": c.trang_thai,
        "ten_kho": c.ten_kho,
        "warehouse_id": c.warehouse_id,
        "ma_kien_k": c.ma_kien_k,
        "ma_f_cha": c.ma_f_cha,
        "ma_thung": c.ma_thung,
        "nguoi_nhan": c.nguoi_nhan,
        "sdt_nguoi_nhan": c.sdt_nguoi_nhan,
        "dia_chi_nhan": c.dia_chi_nhan,
        "nha_van_chuyen": c.nha_van_chuyen,
        "so_luong": c.so_luong,
        "tong_tien_vnd": c.tong_tien_vnd,
        "ngay_tao_kinkin": c.ngay_tao_kinkin.isoformat() if c.ngay_tao_kinkin else None,
        "ngay_cap_nhat_kinkin": c.ngay_cap_nhat_kinkin.isoformat() if c.ngay_cap_nhat_kinkin else None,
        "last_sync_luc": c.last_sync_luc.isoformat() if c.last_sync_luc else None,
        "last_sync_loi": c.last_sync_loi,
    }


@router.get("/lookup/{code}")
def api_lookup(code: str, session: Session = Depends(get_db)) -> dict:
    """Tra cứu mã: ĐỌC từ DB cache (cache_kinkin_ma + du_lieu_sheet), KHÔNG call API live.

    Worker cron nạp cache mỗi 5 phút; UI chỉ render từ DB.
    """
    code = code.strip()
    if not code:
        raise HTTPException(400, "Thiếu code")

    dong = _dong_sheet_theo_code(session, code)
    cache = doc_cache(session, code)

    return {
        "code": code,
        "loai": loai_ma(code),
        "local": _local_to_dict(dong) if dong else None,
        "kinkin": _cache_to_dict(cache) if cache else None,
        "co_cache": cache is not None,
        "trang_thai_cache": (
            "chua_co"
            if cache is None
            else ("loi" if cache.last_sync_loi else ("trong" if not cache.ma_don_chinh else "ok"))
        ),
    }


@router.post("/refresh/{code}")
def api_refresh(code: str, session: Session = Depends(get_db)) -> dict:
    """Force refresh cache cho 1 mã ngay (call Kinkin API, upsert cache)."""
    code = code.strip()
    if not code:
        raise HTTPException(400, "Thiếu code")
    kq = prefetch_code(session, code)
    session.commit()
    return kq
