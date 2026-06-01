from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.integrations import kinkin_client as kk
from app.integrations.kinkin_client import KinkinError
from app.models import DuLieuSheet


def loai_ma(code: str) -> str:
    """Auto-detect prefix code → F / VK / K / PGH / HD / GKA / unknown."""
    s = (code or "").strip().upper()
    if s.startswith("PGH"):
        return "PGH"
    if s.startswith("HD"):
        return "HD"
    if s.startswith("GKA"):
        return "GKA"
    if s.startswith("VK"):
        return "VK"
    if s.startswith("F") and len(s) >= 2 and s[1].isdigit():
        return "F"
    if s.startswith("K") and len(s) >= 2 and s[1].isdigit():
        return "K"
    if "-" in s and len(s) >= 8:
        return "K"
    return "unknown"


def _co_du_lieu(resp: Any) -> bool:
    """Heuristic: response Kinkin có data thực không (không chỉ empty list/null)."""
    if resp is None:
        return False
    if isinstance(resp, dict):
        data = resp.get("data") if "data" in resp else resp
        if isinstance(data, dict):
            inner = (
                data.get("items")
                or data.get("results")
                or data.get("list")
                or data.get("packageFs")
                or data.get("packageVks")
                or data.get("packageKs")
                or data.get("deliveryOrders")
            )
            if inner is not None:
                return bool(inner)
            return bool(data)
        if isinstance(data, list):
            return len(data) > 0
        return bool(data)
    return True


def _thu_qua_kho(api_fn, *args, **kwargs) -> tuple[Optional[Any], Optional[str], list[str]]:
    """Gọi api_fn(warehouse_id=...) qua mọi warehouse trong env, trả response đầu tiên có data.

    Returns: (response, warehouse_id_match, ds_kho_da_thu)
    """
    da_thu: list[str] = []
    fallback_resp = None
    fallback_kho = None

    for wh in settings.kk_warehouse_ids:
        da_thu.append(wh)
        try:
            resp = api_fn(*args, warehouse_id=wh, **kwargs)
        except KinkinError:
            continue
        if _co_du_lieu(resp):
            return resp, wh, da_thu
        if fallback_resp is None:
            fallback_resp = resp
            fallback_kho = wh

    return fallback_resp, fallback_kho, da_thu


def lookup_code(session: Session, code: str) -> dict[str, Any]:
    """Tra cứu code (auto-detect K/VK/F/PGH/GKA) → trả thông tin kết hợp Kinkin + DB."""
    result: dict[str, Any] = {
        "code": code,
        "loai": loai_ma(code),
        "local": None,
        "kinkin": None,
        "loi": None,
        "kho_match": None,
        "kho_da_thu": [],
    }

    dong = session.execute(
        select(DuLieuSheet).where(DuLieuSheet.ma_van_don == code).limit(1)
    ).scalars().first()
    if dong is None:
        dong = session.execute(
            select(DuLieuSheet).where(DuLieuSheet.ma_thung == code).order_by(DuLieuSheet.id.desc()).limit(1)
        ).scalars().first()
    if dong is None:
        dong = session.execute(
            select(DuLieuSheet).where(DuLieuSheet.ma_f_cha == code).order_by(DuLieuSheet.id.desc()).limit(1)
        ).scalars().first()
    if dong is None:
        dong = session.execute(
            select(DuLieuSheet).where(DuLieuSheet.ma_kien_k == code).order_by(DuLieuSheet.id.desc()).limit(1)
        ).scalars().first()

    if dong is not None:
        result["local"] = {
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

    if not settings.KK_USERNAME or not settings.KK_PASSWORD:
        result["loi"] = "Thiếu KK_USERNAME / KK_PASSWORD trong .env"
        return result

    try:
        loai = result["loai"]
        if loai == "F":
            resp, kho, da_thu = _thu_qua_kho(kk.f_list, code)
            result["kinkin"] = {"f_list": resp}
            result["kho_match"] = kho
            result["kho_da_thu"] = da_thu
        elif loai == "VK":
            result["kinkin"] = {"vk_list": kk.vk_list(code)}
        elif loai == "K":
            resp, kho, da_thu = _thu_qua_kho(kk.k_list, code)
            kinkin_payload: dict[str, Any] = {"k_list": resp}
            result["kho_match"] = kho
            result["kho_da_thu"] = da_thu
            if settings.KK_PACKAGEK_APIKEY:
                try:
                    kinkin_payload["k_history"] = kk.k_history(code)
                except KinkinError as e:
                    kinkin_payload["k_history_loi"] = str(e)
            result["kinkin"] = kinkin_payload
        elif loai in ("PGH", "HD"):
            result["kinkin"] = {"pgh_detail": kk.pgh_detail_by_code(code)}
        elif loai == "GKA":
            resp, kho, da_thu = _thu_qua_kho(kk.pgh_list, search_content=code, page=1, page_size=10)
            result["kinkin"] = {"pgh_search": resp}
            result["kho_match"] = kho
            result["kho_da_thu"] = da_thu
        else:
            result["loi"] = f"Không nhận diện được loại mã: {code}"
    except KinkinError as e:
        result["loi"] = str(e)

    return result
