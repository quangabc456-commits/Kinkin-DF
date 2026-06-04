"""Tạo PGH hệ KHO ĐẾN (*.vanchuyenkinkin.com) qua màn hình cho user điền thông tin.

Luồng:
  GET  /pgh/kho-den/{ds_id}   → màn hình điền: map sẵn từ du_lieu_sheet, tra khách →
                                 địa chỉ đã có + kiện F + (tuỳ chọn) đối tác VTP.
  POST /pgh/kho-den/{ds_id}   → tạo PGH kho đến (+ VTP nếu chọn partner) trong 1 call
                                 add-update-delivery → GHI phieu_giao_hang → trang kết quả.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.core.templates import templates
from app.integrations import khoden_client as kc
from app.integrations import quanly_client as qc
from app.integrations.khoden_client import KhodenError
from app.integrations.quanly_client import QuanlyError
from app.models import DuLieuSheet, PhieuGiaoHang
from app.services import kho_den_ref_doc as doc
from app.services.tao_pgh_hop_nhat import luu_ket_qua
from app.services.tao_pgh_kho_den import (
    KhoDenServiceError,
    tao_pgh_dia_chi_cu,
    tao_pgh_dia_chi_moi,
)


router = APIRouter(prefix="/pgh/kho-den", tags=["pgh-kho-den"])


def _can_nang_float(ds: DuLieuSheet) -> float:
    v = ds.can_nang_kg if ds.can_nang_kg is not None else ds.can_nang_kien_kg
    try:
        return float(v) if v is not None else 0.0
    except (TypeError, ValueError):
        return 0.0


def _tim_khach(session: Session, term: str) -> list[dict]:
    """Tra khách GIỐNG trang Danh sách khách hàng (gateway list-server-side-parent,
    searchAll = TÊN/mã thật) → fallback core get-list-customer-by-search → fallback cache.

    Gateway list ưu tiên vì `name` là TÊN THẬT (gõ tên khớp được); core/cache chủ yếu theo mã.
    """
    term = (term or "").strip()
    if not term:
        return []
    try:
        gw = qc.tim_khach_list(term)
        if gw:
            return gw
    except (QuanlyError, KhodenError):
        pass
    try:
        live = kc.tim_khach(term)
        if live:
            return live
    except KhodenError:
        pass
    return doc.tim_khach(session, term, limit=25)


@router.get("/api/khach", response_class=JSONResponse)
def api_tim_khach(q: str = "", session: Session = Depends(get_db)):
    """Typeahead tra khách (live core → fallback cache). Trả [{code, name, phone}].

    value = code → submit lại resolve chính xác. Tên hiển thị ưu tiên displayName/name.
    """
    rows = _tim_khach(session, q)
    return [
        {
            "code": r.get("code"),
            "name": r.get("name") or r.get("displayName"),  # ưu tiên TÊN THẬT (gateway list)
            "phone": r.get("phone"),
        }
        for r in rows
    ]


@router.get("/{ds_id}", response_class=HTMLResponse)
def form_tao_pgh(
    ds_id: int,
    request: Request,
    customer_code: Optional[str] = None,
    session: Session = Depends(get_db),
):
    ds = session.get(DuLieuSheet, ds_id)
    if ds is None:
        raise HTTPException(404, f"Không tìm thấy vận đơn id={ds_id}")

    code = (customer_code or ds.ten_kh or "").strip()
    ctx = {
        "request": request,
        "ds": ds,
        "customer_code": code,
        "khach": None,
        "candidates": [],
        "khach_chua_co": False,
        "quanly_khach_url": settings.KK_QUANLY_BASE.rstrip("/") + "/khach-hang/danh-sach-khach-hang",
        "addresses": [],
        "packages": [],
        "tinhs": [],
        "doi_tac": [],
        "khos": [],
        "vtp_partner_id": settings.VIETTELPOST_PARTNER_ID,
        "loi_cau_hinh": None,
        "loi_khach": None,
        "loi_dia_chi": None,
        "loi_kien": None,
    }

    # ===== Tra khách như trang Danh sách khách hàng (tên thật) → resolve GUID khi chọn =====
    khach = None
    if code:
        matches = _tim_khach(session, code)
        exact = next(
            (m for m in matches if (m.get("code") or "").strip().upper() == code.upper()),
            None,
        )
        chosen = exact or (matches[0] if len(matches) == 1 else None)
        if chosen is not None:
            # list gateway chỉ có id INT → resolve code→GUID (core) để lấy địa chỉ + tạo PGH
            full = None
            try:
                full = kc.lay_customer_id(chosen.get("code") or code)
            except KhodenError:
                full = None
            khach = full or chosen
            # giữ TÊN THẬT từ danh sách khách (core hay để name = mã)
            if khach is full and chosen.get("name") and chosen["name"] != chosen.get("code"):
                khach["name"] = chosen["name"]
        elif len(matches) > 1:
            ctx["candidates"] = matches  # nhiều khớp → cho user chọn
        else:
            # KHÔNG có trong danh sách khách → báo TẠO TÀI KHOẢN cho khách hàng
            ctx["khach_chua_co"] = True

    if khach is not None:
        ctx["khach"] = khach
        # Địa chỉ đã có: đọc cache trước (nhanh). Cache trống cho khách này → thử live
        # (cache địa chỉ chưa đầy đủ); thiếu token thì bỏ qua, KHÔNG chặn trang.
        ctx["addresses"] = doc.dia_chi_cua_khach(session, khach["id"])
        if not ctx["addresses"]:
            try:
                ctx["addresses"] = kc.lay_dia_chi_cua_khach(khach["id"])
            except KhodenError:
                pass
        # Kiện F: GIỮ LIVE (volatile) — cần token; thiếu token → báo ở ô kiện, không chặn cả trang
        try:
            ctx["packages"] = kc.ds_kien_f(khach.get("code") or code)
        except KhodenError as e:
            ctx["loi_kien"] = str(e)

    # Tỉnh + kho: đọc từ cache (cho datalist / select kho gửi)
    ctx["tinhs"] = doc.ds_tinh(session)
    ctx["khos"] = doc.ds_kho(session)
    # Đối tác VTP qua gateway (1-call). Thiếu token → fallback list tĩnh để form vẫn render.
    try:
        ctx["doi_tac"] = qc.ds_doi_tac()
    except (QuanlyError, KhodenError):
        ctx["doi_tac"] = [{"id": settings.VIETTELPOST_PARTNER_ID, "name": "Viettel Post"}]

    return templates.TemplateResponse("pgh/kho_den_form.html", ctx)


@router.post("/{ds_id}", response_class=HTMLResponse)
def submit_tao_pgh(
    ds_id: int,
    request: Request,
    customer_code: str = Form(...),
    che_do_dia_chi: str = Form("cu"),  # "cu" = địa chỉ đã có | "moi" = tạo địa chỉ mới
    address_id: str = Form(""),
    receiver: str = Form(""),
    receive_phone: str = Form(""),
    ten_tinh: str = Form(""),
    ten_huyen: str = Form(""),
    ten_xa: str = Form(""),
    address: str = Form(""),
    package_tokens: list[str] = Form([]),  # "packageFId|packageFCode"
    delivery_method_id: int = Form(2),
    note: str = Form(""),
    received_date: str = Form(""),
    is_draft: bool = Form(False),
    # ----- VTP (tuỳ chọn, tạo đồng thời trong 1 call qua partner*) -----
    delivery_partner_id: int = Form(0),
    vtp_service: str = Form(""),
    vtp_payment: str = Form(""),
    vtp_cod: str = Form(""),
    vtp_price: str = Form(""),
    vtp_product_name: str = Form(""),
    vtp_length: str = Form(""),
    vtp_width: str = Form(""),
    vtp_height: str = Form(""),
    vtp_warehouse_phone: str = Form(""),
    vtp_warehouse_address: str = Form(""),
    vtp_warehouse_name: str = Form(""),
    session: Session = Depends(get_db),
):
    ds = session.get(DuLieuSheet, ds_id)
    if ds is None:
        raise HTTPException(404, f"Không tìm thấy vận đơn id={ds_id}")

    customer_code = customer_code.strip()
    packages: list[dict] = []
    for tok in package_tokens:
        fid, _, ftk = tok.partition("|")
        if fid:
            packages.append({"packageFId": fid, "codeTracking": ftk})

    ctx_base = {
        "request": request,
        "ds": ds,
        "customer_code": customer_code,
        "che_do_dia_chi": che_do_dia_chi,
    }

    if not packages:
        return templates.TemplateResponse(
            "pgh/kho_den_ket_qua.html",
            {**ctx_base, "ok": False, "loi": "Chưa chọn kiện F nào để lên PGH."},
            status_code=400,
        )

    # Idempotency: nếu vận đơn này đã có PGH kho đến tạo thành công → KHÔNG tạo lại
    # (tránh tạo trùng đơn trên hệ kho đến). Phiếu lỗi trước đó vẫn cho tạo lại.
    da_tao = (
        session.execute(
            select(PhieuGiaoHang).where(
                PhieuGiaoHang.du_lieu_sheet_id == ds.id,
                PhieuGiaoHang.trang_thai_kinkin == "da_tao",
            )
        )
        .scalars()
        .first()
    )
    if da_tao is not None:
        return templates.TemplateResponse(
            "pgh/kho_den_ket_qua.html",
            {
                **ctx_base, "ok": True, "loi": None, "pgh": da_tao,
                "co_vtp": bool(da_tao.ma_pgh_vtp), "da_ton_tai": True,
            },
        )

    # VTP (tuỳ chọn): chỉ tạo đồng thời khi chọn đối tác = Viettel Post
    co_vtp = bool(delivery_partner_id) and delivery_partner_id == settings.VIETTELPOST_PARTNER_ID
    vtp = None
    if co_vtp:
        vtp = {
            "partner_id": delivery_partner_id,
            "service": vtp_service.strip() or None,
            "payment": vtp_payment,
            "cod": vtp_cod,
            "price": vtp_price,
            "product_name": vtp_product_name or ds.nhom_san_pham,
            "length": vtp_length,
            "width": vtp_width,
            "height": vtp_height,
            "warehouse_phone": vtp_warehouse_phone.strip() or None,
            "warehouse_address": vtp_warehouse_address.strip() or None,
            "warehouse_name": vtp_warehouse_name.strip() or None,
        }

    chung = dict(
        packages=packages,
        delivery_method_id=delivery_method_id,
        note=note.strip(),
        received_date=received_date.strip() or None,
        total_weight=_can_nang_float(ds),
        is_draft=is_draft,
        vtp=vtp,
    )

    try:
        if che_do_dia_chi == "moi":
            if not (ten_tinh.strip() and ten_huyen.strip() and ten_xa.strip()):
                raise KhoDenServiceError("Địa chỉ mới: cần đủ Tỉnh / Quận-Huyện / Phường-Xã.")
            if not receiver.strip():
                raise KhoDenServiceError("Địa chỉ mới: thiếu Tên người nhận.")
            if not receive_phone.strip():
                raise KhoDenServiceError("Địa chỉ mới: thiếu SĐT người nhận.")
            if len(address.strip()) < settings.MIN_DIA_CHI_LEN:
                raise KhoDenServiceError(
                    f"Địa chỉ mới: 'Địa chỉ chi tiết' cần tối thiểu {settings.MIN_DIA_CHI_LEN} ký tự."
                )
            kq = tao_pgh_dia_chi_moi(
                customer_code=customer_code,
                receiver=receiver.strip(),
                receive_phone=receive_phone.strip(),
                ten_tinh=ten_tinh.strip(),
                ten_huyen=ten_huyen.strip(),
                ten_xa=ten_xa.strip(),
                address=address.strip(),
                **chung,
            )
        else:
            if not address_id.strip():
                raise KhoDenServiceError("Chưa chọn địa chỉ đã có của khách.")
            kq = tao_pgh_dia_chi_cu(
                customer_code=customer_code,
                address_id=address_id.strip(),
                **chung,
            )
    except (KhoDenServiceError, KhodenError, QuanlyError) as e:
        # Ghi lại thất bại (nếu đã có khách/đơn) để theo dõi trên danh sách
        try:
            luu_ket_qua(
                session, ds, None, ok=False, loi=str(e),
                receiver=receiver.strip(), receive_phone=receive_phone.strip(),
                address=address.strip(), co_vtp=bool(co_vtp),
            )
            session.commit()
        except Exception:
            session.rollback()
        return templates.TemplateResponse(
            "pgh/kho_den_ket_qua.html",
            {**ctx_base, "ok": False, "loi": str(e), "co_vtp": co_vtp},
            status_code=400,
        )

    resp = kq.get("resp") or {}
    # CHỈ coi là OK khi responseStatus thật sự truthy (không default True) — khớp pattern an toàn
    # ở tao_dia_chi. Response 200 thiếu responseStatus → coi là lỗi/không rõ để tránh ghi 'da_tao' giả.
    ok = bool(isinstance(resp, dict) and resp.get("responseStatus"))
    loi = None if ok else f"API trả về lỗi/không rõ trạng thái: {str(resp)[:400]}"

    # API kho đến đã tạo PGH; nếu GHI DB lỗi → cảnh báo orphan thay vì 500
    try:
        pgh = luu_ket_qua(
            session, ds, kq, ok=ok, loi=loi,
            receiver=receiver.strip(), receive_phone=receive_phone.strip(),
            address=address.strip(), co_vtp=bool(co_vtp),
        )
        session.commit()
    except Exception as e:  # noqa: BLE001
        session.rollback()
        return templates.TemplateResponse(
            "pgh/kho_den_ket_qua.html",
            {
                **ctx_base, "ok": False,
                "loi": f"PGH có thể đã tạo trên hệ kho đến NHƯNG ghi DB thất bại: {e}. "
                       f"Kiểm tra/đối soát thủ công. Resp: {str(resp)[:300]}",
                "kq": kq, "resp": resp, "req_body": kq.get("request"),
                "dia_chi": kq.get("dia_chi"), "co_vtp": co_vtp, "db_loi": True,
            },
            status_code=500,
        )

    # Tạo thành công nhưng không lấy được mã PGH từ response (shape chưa xác minh) → cảnh báo
    canh_bao = None
    if ok and not pgh.ma_pgh_kinkin:
        canh_bao = (
            "Tạo thành công nhưng chưa lấy được Mã PGH từ response (shape add-update-delivery "
            "chưa xác minh) — cần kiểm tra trên hệ kho đến."
        )

    return templates.TemplateResponse(
        "pgh/kho_den_ket_qua.html",
        {
            **ctx_base,
            "ok": ok,
            "loi": loi,
            "canh_bao": canh_bao,
            "kq": kq,
            "resp": resp,
            "req_body": kq.get("request"),
            "dia_chi": kq.get("dia_chi"),
            "is_draft": is_draft,
            "co_vtp": co_vtp,
            "pgh": pgh,
        },
    )
