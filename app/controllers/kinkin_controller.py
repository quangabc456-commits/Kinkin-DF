from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models import CacheKinkinMa, DuLieuSheet, PhieuGiaoHang
from app.services.cache_kinkin import doc_cache, prefetch_code
from app.services.kinkin_lookup import loai_ma


router = APIRouter(prefix="/api/kinkin", tags=["kinkin"])

TRA_CUU_LIMIT = 50


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


def _du_lieu_sheet_to_row(d: DuLieuSheet) -> dict:
    return {
        "id": d.id,
        "ten_sheet": d.ten_sheet,
        "ngay_chot": d.ngay_chot.isoformat() if d.ngay_chot else None,
        "ma_kien_k": d.ma_kien_k,
        "ma_f_cha": d.ma_f_cha,
        "ma_thung": d.ma_thung,
        "ma_van_don": d.ma_van_don,
        "ten_kh": d.ten_kh,
        "sdt_nguoi_nhan": d.sdt_nguoi_nhan,
        "dia_chi_nguoi_nhan": d.dia_chi_nguoi_nhan,
        "phuong_thuc_gui": d.phuong_thuc_gui,
        "can_nang_kg": float(d.can_nang_kg) if d.can_nang_kg else None,
        "trang_thai_goc": d.trang_thai_goc,
    }


def _pgh_to_row(p: PhieuGiaoHang) -> dict:
    return {
        "id": p.id,
        "ma_pgh_vtp": p.ma_pgh_vtp,
        "ma_pgh_kinkin": p.ma_pgh_kinkin,
        "ma_pgh_noi_bo": p.ma_pgh_noi_bo,
        "trang_thai_pgh": p.trang_thai_pgh,
        "trang_thai_kinkin": p.trang_thai_kinkin,
        "nguoi_nhan_ten": p.nguoi_nhan_ten,
        "nguoi_nhan_sdt": p.nguoi_nhan_sdt,
        "nguoi_nhan_dia_chi": p.nguoi_nhan_dia_chi,
        "cuoc_tong_vnd": p.cuoc_tong_vnd,
        "kho_den_id": p.kho_den_id,
        "chot_luc": p.chot_luc.isoformat() if p.chot_luc else None,
        "loi_message": p.loi_message,
    }


@router.get("/tra-cuu/{code}")
def api_tra_cuu(code: str, session: Session = Depends(get_db)) -> dict:
    """Tra cứu nhanh: trả kết quả query thẳng theo loại mã (không hiển thị SQL).

    - K          → tất cả dòng cùng kiện K (du_lieu_sheet.ma_kien_k = code)
    - F          → dòng có ma_f_cha HOẶC ma_thung = code
    - GKA / VK   → dòng vận đơn (ma_van_don = code)
    - PGH / HD   → phieu_giao_hang.ma_pgh_vtp = code
    - unknown    → quét cả 4 cột du_lieu_sheet
    """
    code = code.strip()
    if not code:
        raise HTTPException(400, "Thiếu code")
    loai = loai_ma(code)

    rows: list[dict] = []
    bang = "du_lieu_sheet"
    mota = ""

    if loai == "K":
        mota = f"Tất cả dòng cùng kiện K = {code}"
        ds = session.execute(
            select(DuLieuSheet)
            .where(DuLieuSheet.ma_kien_k == code)
            .order_by(DuLieuSheet.ngay_chot.desc(), DuLieuSheet.sheet_row_index)
            .limit(TRA_CUU_LIMIT)
        ).scalars().all()
        rows = [_du_lieu_sheet_to_row(d) for d in ds]

    elif loai == "F":
        mota = f"Dòng có F cha HOẶC thùng = {code}"
        ds = session.execute(
            select(DuLieuSheet)
            .where(or_(DuLieuSheet.ma_f_cha == code, DuLieuSheet.ma_thung == code))
            .order_by(DuLieuSheet.ngay_chot.desc(), DuLieuSheet.sheet_row_index)
            .limit(TRA_CUU_LIMIT)
        ).scalars().all()
        rows = [_du_lieu_sheet_to_row(d) for d in ds]

    elif loai in ("GKA", "VK"):
        mota = f"Vận đơn = {code}"
        ds = session.execute(
            select(DuLieuSheet)
            .where(DuLieuSheet.ma_van_don == code)
            .limit(TRA_CUU_LIMIT)
        ).scalars().all()
        rows = [_du_lieu_sheet_to_row(d) for d in ds]

    elif loai in ("PGH", "HD"):
        mota = f"PGH với mã VTP = {code}"
        bang = "phieu_giao_hang"
        pghs = session.execute(
            select(PhieuGiaoHang)
            .where(PhieuGiaoHang.ma_pgh_vtp == code)
            .limit(TRA_CUU_LIMIT)
        ).scalars().all()
        rows = [_pgh_to_row(p) for p in pghs]

    else:
        mota = f"Quét tất cả cột mã = {code}"
        ds = session.execute(
            select(DuLieuSheet)
            .where(
                or_(
                    DuLieuSheet.ma_van_don == code,
                    DuLieuSheet.ma_thung == code,
                    DuLieuSheet.ma_f_cha == code,
                    DuLieuSheet.ma_kien_k == code,
                )
            )
            .order_by(DuLieuSheet.ngay_chot.desc(), DuLieuSheet.sheet_row_index)
            .limit(TRA_CUU_LIMIT)
        ).scalars().all()
        rows = [_du_lieu_sheet_to_row(d) for d in ds]

    cache = doc_cache(session, code)
    cache_dict = _cache_to_dict(cache) if cache else None

    return {
        "code": code,
        "loai": loai,
        "bang": bang,
        "mota": mota,
        "tong": len(rows),
        "rows": rows,
        "gioi_han": TRA_CUU_LIMIT,
        "cache_kinkin": cache_dict,
    }
