from __future__ import annotations

import secrets
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.integrations.vtp_client import VtpClient, VtpError
from app.models import CauHinh, DuLieuSheet, PhieuGiaoHang, TaiKhoanVtp
from app.services.dia_chi_lookup import lookup_dia_chi


def _get_cau_hinh(session: Session, khoa: str, mac_dinh: str = "") -> str:
    row = session.execute(select(CauHinh).where(CauHinh.khoa == khoa)).scalar_one_or_none()
    return row.gia_tri if row and row.gia_tri else mac_dinh


def _sinh_ma_noi_bo() -> str:
    return "KK" + datetime.now().strftime("%y%m%d") + secrets.token_hex(4).upper()


def _can_kg_sang_gram(v: Optional[Decimal]) -> int:
    if v is None:
        return 50
    g = int(v * 1000)
    return max(g, 50)


def chuan_bi_body_nlp(
    session: Session,
    dong_sheet: DuLieuSheet,
    pgh: PhieuGiaoHang,
    sender_fullname: str,
    sender_phone: str,
    sender_address: str,
) -> dict:
    """Build body cho POST /v2/order/createOrderNlp (địa chỉ chi tiết, không cần ID)."""
    body = {
        "ORDER_NUMBER": pgh.ma_pgh_noi_bo,
        "SENDER_FULLNAME": sender_fullname,
        "SENDER_ADDRESS": sender_address,
        "SENDER_PHONE": sender_phone,
        "RECEIVER_FULLNAME": pgh.nguoi_nhan_ten,
        "RECEIVER_ADDRESS": pgh.nguoi_nhan_dia_chi,
        "RECEIVER_PHONE": pgh.nguoi_nhan_sdt,
        "PRODUCT_NAME": pgh.san_pham_ten or "Hàng hóa",
        "PRODUCT_QUANTITY": pgh.san_pham_so_luong,
        "PRODUCT_PRICE": pgh.san_pham_gia_vnd,
        "PRODUCT_WEIGHT": pgh.san_pham_can_nang_gram or _can_kg_sang_gram(dong_sheet.can_nang_kg),
        "PRODUCT_LENGTH": pgh.san_pham_dai_cm or 0,
        "PRODUCT_WIDTH": pgh.san_pham_rong_cm or 0,
        "PRODUCT_HEIGHT": pgh.san_pham_cao_cm or 0,
        "ORDER_PAYMENT": pgh.hinh_thuc_tt,
        "ORDER_SERVICE": pgh.dich_vu_chinh,
        "PRODUCT_TYPE": pgh.loai_hang,
        "ORDER_SERVICE_ADD": pgh.dich_vu_cong_them or None,
        "ORDER_NOTE": (pgh.ghi_chu_pgh or "")[:150],
        "MONEY_COLLECTION": pgh.tien_thu_ho_vnd,
        "EXTRA_MONEY": pgh.tien_xem_hang_vnd,
        "CHECK_UNIQUE": True,
        "ENABLE_SORT_CODE": True,
        "PRODUCT_DETAIL": [
            {
                "PRODUCT_NAME": pgh.san_pham_ten or "Hàng hóa",
                "PRODUCT_QUANTITY": pgh.san_pham_so_luong,
                "PRODUCT_PRICE": pgh.san_pham_gia_vnd,
                "PRODUCT_WEIGHT": pgh.san_pham_can_nang_gram
                or _can_kg_sang_gram(dong_sheet.can_nang_kg),
            }
        ],
    }
    return body


def tao_pgh_tu_dong_sheet(
    session: Session,
    du_lieu_sheet_id: int,
    tai_khoan_vtp_id: Optional[int] = None,
    sender_fullname: str = "",
    sender_phone: str = "",
    sender_address: str = "",
    user: str = "system",
) -> PhieuGiaoHang:
    dong = session.get(DuLieuSheet, du_lieu_sheet_id)
    if dong is None:
        raise ValueError(f"Không tìm thấy du_lieu_sheet id={du_lieu_sheet_id}")

    existing = (
        session.execute(
            select(PhieuGiaoHang).where(
                PhieuGiaoHang.du_lieu_sheet_id == dong.id,
                PhieuGiaoHang.ma_pgh_vtp.is_not(None),
            )
        )
        .scalars()
        .first()
    )
    if existing is not None:
        raise ValueError(f"Dòng id={dong.id} đã có PGH {existing.ma_pgh_vtp}")

    if tai_khoan_vtp_id is None:
        tk = session.execute(
            select(TaiKhoanVtp).where(
                TaiKhoanVtp.mac_dinh.is_(True), TaiKhoanVtp.kich_hoat.is_(True)
            )
        ).scalar_one_or_none()
        if tk is None:
            tk = session.execute(
                select(TaiKhoanVtp).where(TaiKhoanVtp.kich_hoat.is_(True))
            ).scalar_one_or_none()
        if tk is None:
            raise ValueError("Chưa có tài khoản VTP nào trong DB")
    else:
        tk = session.get(TaiKhoanVtp, tai_khoan_vtp_id)
        if tk is None:
            raise ValueError(f"Không tìm thấy tai_khoan_vtp id={tai_khoan_vtp_id}")

    dich_vu_chinh = _get_cau_hinh(session, "DEFAULT_ORDER_SERVICE", "VCN")
    hinh_thuc_tt = int(_get_cau_hinh(session, "DEFAULT_ORDER_PAYMENT", "1"))

    lookup = lookup_dia_chi(session, dong.dia_chi_nguoi_nhan or "")

    pgh = PhieuGiaoHang(
        du_lieu_sheet_id=dong.id,
        tai_khoan_vtp_id=tk.id,
        ma_pgh_noi_bo=_sinh_ma_noi_bo(),
        trang_thai_pgh="cho_chot",
        nguoi_nhan_ten=dong.ten_kh or "Khách",
        nguoi_nhan_sdt=dong.sdt_nguoi_nhan or "0000000000",
        nguoi_nhan_dia_chi=dong.dia_chi_nguoi_nhan or "",
        nguoi_nhan_tinh_id=lookup.tinh_id,
        nguoi_nhan_huyen_id=lookup.huyen_id,
        nguoi_nhan_xa_id=lookup.xa_id,
        san_pham_ten=dong.nhom_san_pham or "Hàng hóa",
        san_pham_so_luong=1,
        san_pham_gia_vnd=0,
        san_pham_can_nang_gram=_can_kg_sang_gram(dong.can_nang_kg),
        loai_hang="HH",
        hinh_thuc_tt=hinh_thuc_tt,
        dich_vu_chinh=dich_vu_chinh,
        tien_thu_ho_vnd=0,
        ghi_chu_pgh=dong.ghi_chu or "",
        chot_boi=user,
    )
    session.add(pgh)
    session.flush()

    body = chuan_bi_body_nlp(session, dong, pgh, sender_fullname, sender_phone, sender_address)
    pgh.vtp_request_json = body

    client = VtpClient(session, tk)
    try:
        data = client.tao_pgh_nlp(body, phieu_giao_hang_id=pgh.id)
    except VtpError as e:
        pgh.trang_thai_pgh = "loi_api"
        pgh.loi_message = str(e)
        session.flush()
        raise

    pgh.ma_pgh_vtp = data.get("ORDER_NUMBER")
    pgh.vtp_response_json = data
    pgh.cuoc_tong_vnd = data.get("MONEY_TOTAL")
    pgh.cuoc_chinh_vnd = data.get("MONEY_TOTAL_FEE")
    pgh.phi_xang_dau_vnd = data.get("MONEY_FEE")
    pgh.phi_thu_ho_vnd = data.get("MONEY_COLLECTION_FEE")
    pgh.phi_khac_vnd = data.get("MONEY_OTHER_FEE")
    pgh.vat_vnd = data.get("MONEY_VAT")
    pgh.kpi_giao_gio = Decimal(str(data["KPI_HT"])) if data.get("KPI_HT") is not None else None
    pgh.can_quy_doi_gram = data.get("EXCHANGE_WEIGHT")
    pgh.sort_code = data.get("SORT_CODE")
    pgh.trang_thai_pgh = "da_chot"
    pgh.chot_luc = datetime.now(timezone.utc)
    if data.get("RECEIVER_PROVINCE") and pgh.nguoi_nhan_tinh_id is None:
        pgh.nguoi_nhan_tinh_id = data["RECEIVER_PROVINCE"]
    if data.get("RECEIVER_DISTRICT") and pgh.nguoi_nhan_huyen_id is None:
        pgh.nguoi_nhan_huyen_id = data["RECEIVER_DISTRICT"]
    if data.get("RECEIVER_WARD") and pgh.nguoi_nhan_xa_id is None:
        pgh.nguoi_nhan_xa_id = data["RECEIVER_WARD"]

    session.flush()
    return pgh
