"""Tạo PGH hệ KHO ĐẾN (*.vanchuyenkinkin.com) qua màn hình cho user điền thông tin.

Luồng:
  GET  /pgh/kho-den/{ds_id}   → màn hình điền: map sẵn từ du_lieu_sheet, tra khách →
                                 địa chỉ đã có + kiện F + (tuỳ chọn) đối tác VTP.
  POST /pgh/kho-den/{ds_id}   → tạo PGH kho đến (+ VTP nếu chọn partner) trong 1 call
                                 add-update-delivery → GHI phieu_giao_hang → trang kết quả.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import date
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


def _la_guid(v) -> bool:
    """id GUID (get-customer-code/core) vs id INT (list-server-side-parent)."""
    return isinstance(v, str) and len(v) >= 32 and "-" in v


def _tim_khach(session: Session, term: str) -> list[dict]:
    """Tra khách — ƯU TIÊN DB (cron giữ tươi mỗi 10') để hiển thị TỨC THÌ:
      1) DB kd_khach_hang: khớp mã & tên; 1 mã gốc (vd 093HN) → nhiều khách con qua ILIKE;
         có sẵn GUID để tạo phiếu ngay.
      2) Khách MỚI chưa kịp đồng bộ → hỏi trực tiếp hệ thống (theo mã kèm khách con, rồi theo tên).
    """
    term = (term or "").strip()
    if not term:
        return []
    db = doc.tim_khach(session, term, limit=25)
    if db:
        return db
    for fn in (lambda: qc.tim_khach(term), lambda: qc.tim_khach_list(term)):
        try:
            r = fn()
            if r:
                return r
        except (QuanlyError, KhodenError):
            pass
    try:
        live = kc.tim_khach(term)
        if live:
            return live
    except KhodenError:
        pass
    return []


def _resolve_orderable(code: str):
    """code → khách orderable (có GUID) để tạo PGH. get-customer-code trước (đúng GUID +
    bắt khách con), core sau. Trả dict (1 khách), HOẶC list (mã có nhiều con → cho chọn),
    HOẶC None (không resolve được).
    """
    code = (code or "").strip()
    try:
        r = qc.tim_khach(code)
    except (QuanlyError, KhodenError):
        r = []
    if r:
        exact = next((m for m in r if (m.get("code") or "").strip().upper() == code.upper()), None)
        if exact is not None:
            return exact
        return r[0] if len(r) == 1 else r  # nhiều con → list
    try:
        return kc.lay_customer_id(code)
    except KhodenError:
        return None


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
    warehouse_id: int = 0,  # Kho đến đang chọn (0 = mặc định) — lọc kiện F theo kho
    session: Session = Depends(get_db),
):
    ds = session.get(DuLieuSheet, ds_id)
    if ds is None:
        raise HTTPException(404, f"Không tìm thấy vận đơn id={ds_id}")

    # Chỉ tra khi user thực sự nhập mã/tên (KHÔNG auto theo ten_kh — đơn Viettel ten_kh là
    # người nhận, không phải mã khách → tránh báo nhầm "khách chưa có" ngay khi mở trang).
    code = (customer_code or "").strip()
    cur_warehouse_id = warehouse_id or int(settings.DEFAULT_KHO_DEN_ID or 5)
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
        "nguoi_tao": settings.KK_KHODEN_USERNAME or "—",
        "hom_nay": date.today().strftime("%d/%m/%Y"),
        "cur_warehouse_id": cur_warehouse_id,
        "tong_kien": 0,
        "tong_can": 0.0,
        "loi_cau_hinh": None,
        "loi_khach": None,
        "loi_dia_chi": None,
        "loi_kien": None,
    }

    # ===== Tra khách: get-customer-code (mã + khách con) / list (tên) → đảm bảo GUID orderable =====
    khach = None
    if code:
        matches = _tim_khach(session, code)
        exact = next(
            (m for m in matches if (m.get("code") or "").strip().upper() == code.upper()),
            None,
        )
        chosen = exact or (matches[0] if len(matches) == 1 else None)
        if chosen is not None:
            if _la_guid(chosen.get("id")):
                khach = chosen  # đã orderable (get-customer-code/core)
            else:
                # chosen từ list parent (id INT) → resolve code→GUID (có thể ra nhiều khách con)
                r = _resolve_orderable(chosen.get("code") or code)
                if isinstance(r, list):
                    ctx["candidates"] = r  # 1 mã → nhiều khách con → cho chọn
                else:
                    khach = r or chosen
                    if khach and chosen.get("name") and not khach.get("name"):
                        khach["name"] = chosen["name"]
        elif len(matches) > 1:
            ctx["candidates"] = matches  # nhiều khớp (gồm khách con cùng mã gốc) → cho chọn
        else:
            ctx["khach_chua_co"] = True  # không có trong danh sách → báo tạo tài khoản

    # Danh mục đọc DB (nhanh) — luôn cần cho select Kho đến + datalist Tỉnh
    ctx["tinhs"] = doc.ds_tinh(session)
    ctx["khos"] = doc.ds_kho(session)

    if khach is not None:
        ctx["khach"] = khach
        ctx["addresses"] = doc.dia_chi_cua_khach(session, khach["id"])  # cache (DB, nhanh)

        # Các call LIVE độc lập chạy SONG SONG (không đụng DB session) → thời gian ~= 1 call
        # chậm nhất thay vì tổng. Mở trang trống (chưa có khách) thì KHÔNG gọi live nào.
        def _lay_kien():
            # CHỈ kiện F chưa lên phiếu (endpoint tự lọc bỏ F đã tạo phiếu/đã giao)
            return kc.ds_kien_f_kha_dung(khach.get("code") or code)

        def _lay_doi_tac():
            try:
                return qc.ds_doi_tac()
            except (QuanlyError, KhodenError):
                return [{"id": settings.VIETTELPOST_PARTNER_ID, "name": "Viettel Post"}]

        def _lay_dia_chi_live():
            try:
                return kc.lay_dia_chi_cua_khach(khach["id"])
            except KhodenError:
                return []

        with ThreadPoolExecutor(max_workers=3) as ex:
            fut_kien = ex.submit(_lay_kien)        # kiện F (live, volatile)
            fut_dt = ex.submit(_lay_doi_tac)       # đối tác VTP (cache 30')
            fut_addr = ex.submit(_lay_dia_chi_live) if not ctx["addresses"] else None
            try:
                ctx["packages"] = fut_kien.result()
            except KhodenError as e:
                ctx["loi_kien"] = str(e)
            ctx["doi_tac"] = fut_dt.result()
            if fut_addr is not None:
                addr = fut_addr.result()
                if addr:
                    ctx["addresses"] = addr

        ctx["tong_kien"] = len(ctx["packages"])
        ctx["tong_can"] = round(sum(float(p.get("packageFWeight") or 0) for p in ctx["packages"]), 2)

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
    warehouse_id: int = Form(0),  # Kho đến (0 = dùng mặc định)
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
            {**ctx_base, "ok": False, "loi": "Bạn chưa chọn kiện F nào để lên phiếu."},
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
        warehouse_id=(warehouse_id or None),
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
    loi = None if ok else "Hệ thống chưa tạo được phiếu (phản hồi chưa rõ). Vui lòng thử lại, hoặc kiểm tra lại trên hệ kho đến."

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
                "loi": "Phiếu có thể đã được tạo trên hệ kho đến nhưng lưu lại chưa thành công. "
                       "Vui lòng kiểm tra/đối soát thủ công trên hệ kho đến.",
                "kq": kq, "resp": resp, "req_body": kq.get("request"),
                "dia_chi": kq.get("dia_chi"), "co_vtp": co_vtp, "db_loi": True,
            },
            status_code=500,
        )

    # Tạo thành công nhưng không lấy được mã PGH từ response (shape chưa xác minh) → cảnh báo
    canh_bao = None
    if ok and not pgh.ma_pgh_kinkin:
        canh_bao = (
            "Đã tạo phiếu nhưng chưa lấy được Mã phiếu — vui lòng kiểm tra lại trên hệ kho đến."
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
