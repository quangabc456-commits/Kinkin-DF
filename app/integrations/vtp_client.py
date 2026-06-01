from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import LogApiVtp, TaiKhoanVtp


class VtpError(Exception):
    pass


class VtpClient:
    """Thin wrapper around ViettelPost partner API.

    Token strategy:
    - Nếu `tai_khoan_vtp.secret_token` có giá trị → dùng endpoint /v2/user/LoginVTP
      để đổi sang token dùng được (1-2 năm).
    - Ngược lại nếu có username/password → /v2/user/Login → /v2/user/ownerconnect.
    """

    TIMEOUT = 30.0

    def __init__(
        self, session: Session, tai_khoan: TaiKhoanVtp, base_url: Optional[str] = None
    ) -> None:
        self.session = session
        self.tai_khoan = tai_khoan
        self.base_url = base_url or settings.VTP_BASE_URL

    def _client(self) -> httpx.Client:
        return httpx.Client(base_url=self.base_url, timeout=self.TIMEOUT)

    def _log(
        self,
        endpoint: str,
        method: str,
        request_body: Any,
        response: Optional[httpx.Response],
        loi: Optional[str] = None,
        phieu_giao_hang_id: Optional[int] = None,
    ) -> None:
        resp_json = None
        if response is not None:
            try:
                resp_json = response.json()
            except Exception:
                resp_json = {"_text": response.text[:2000]}
        entry = LogApiVtp(
            endpoint=endpoint,
            method=method,
            request_body=request_body if isinstance(request_body, (dict, list)) else None,
            response_body=resp_json if isinstance(resp_json, (dict, list)) else None,
            http_status=response.status_code if response is not None else None,
            loi_message=loi,
            tai_khoan_vtp_id=self.tai_khoan.id,
            phieu_giao_hang_id=phieu_giao_hang_id,
        )
        self.session.add(entry)

    def _token_con_han(self) -> bool:
        if not self.tai_khoan.token_hien_tai:
            return False
        if not self.tai_khoan.token_het_han_luc:
            return True
        return self.tai_khoan.token_het_han_luc > datetime.now(timezone.utc) + timedelta(minutes=5)

    def lay_token(self, ep_refresh: bool = False) -> str:
        if not ep_refresh and self._token_con_han():
            return self.tai_khoan.token_hien_tai  # type: ignore[return-value]

        if self.tai_khoan.secret_token:
            token = self._login_secret(self.tai_khoan.secret_token)
        elif self.tai_khoan.username and self.tai_khoan.password_enc:
            from app.core.security import giai_ma

            pwd = giai_ma(self.tai_khoan.password_enc)
            token = self._login_user_pass(self.tai_khoan.username, pwd)
        else:
            raise VtpError("Tài khoản VTP chưa có credential (secret_token hoặc username/password)")

        self.tai_khoan.token_hien_tai = token
        self.tai_khoan.token_het_han_luc = datetime.now(timezone.utc) + timedelta(days=300)
        self.session.flush()
        return token

    def _login_secret(self, secret: str) -> str:
        body = {"token": secret}
        with self._client() as c:
            r = c.post("/v2/user/LoginVTP", json=body)
        self._log("/v2/user/LoginVTP", "POST", body, r)
        if r.status_code != 200:
            raise VtpError(f"LoginVTP {r.status_code}: {r.text}")
        data = r.json()
        if data.get("error"):
            raise VtpError(f"LoginVTP: {data.get('message')}")
        return data["data"]["token"]

    def _login_user_pass(self, username: str, password: str) -> str:
        body = {"USERNAME": username, "PASSWORD": password}
        with self._client() as c:
            r = c.post("/v2/user/Login", json=body)
            self._log("/v2/user/Login", "POST", body, r)
            if r.status_code != 200:
                raise VtpError(f"Login {r.status_code}: {r.text}")
            data = r.json()
            if data.get("error"):
                raise VtpError(f"Login: {data.get('message')}")
            short_token = data["data"]["token"]

            r2 = c.post("/v2/user/ownerconnect", json=body, headers={"Token": short_token})
        self._log("/v2/user/ownerconnect", "POST", body, r2)
        if r2.status_code != 200:
            raise VtpError(f"ownerconnect {r2.status_code}: {r2.text}")
        data2 = r2.json()
        if data2.get("error"):
            raise VtpError(f"ownerconnect: {data2.get('message')}")
        return data2["data"]["token"]

    def _headers(self) -> dict:
        return {"Token": self.lay_token(), "Content-Type": "application/json"}

    def tao_pgh_nlp(self, body: dict, phieu_giao_hang_id: Optional[int] = None) -> dict:
        endpoint = "/v2/order/createOrderNlp"
        with self._client() as c:
            r = c.post(endpoint, json=body, headers=self._headers())
        self._log(endpoint, "POST", body, r, phieu_giao_hang_id=phieu_giao_hang_id)
        try:
            data = r.json()
        except Exception:
            raise VtpError(f"VTP trả response không phải JSON: {r.text[:500]}")
        if r.status_code != 200 or data.get("error"):
            raise VtpError(f"createOrderNlp: {data.get('message') or r.text[:500]}")
        return data.get("data") or {}

    def tao_pgh_id(self, body: dict, phieu_giao_hang_id: Optional[int] = None) -> dict:
        endpoint = "/v2/order/createOrder"
        with self._client() as c:
            r = c.post(endpoint, json=body, headers=self._headers())
        self._log(endpoint, "POST", body, r, phieu_giao_hang_id=phieu_giao_hang_id)
        try:
            data = r.json()
        except Exception:
            raise VtpError(f"VTP trả response không phải JSON: {r.text[:500]}")
        if r.status_code != 200 or data.get("error"):
            raise VtpError(f"createOrder: {data.get('message') or r.text[:500]}")
        return data.get("data") or {}

    def cap_nhat_trang_thai(self, ma_van_don: str, loai: int, ghi_chu: str = "") -> dict:
        endpoint = "/v2/order/UpdateOrder"
        body = {"TYPE": loai, "ORDER_NUMBER": ma_van_don, "NOTE": ghi_chu[:150]}
        with self._client() as c:
            r = c.post(endpoint, json=body, headers=self._headers())
        self._log(endpoint, "POST", body, r)
        try:
            data = r.json()
        except Exception:
            raise VtpError(f"VTP trả response không phải JSON: {r.text[:500]}")
        if r.status_code != 200 or data.get("error"):
            raise VtpError(f"UpdateOrder: {data.get('message') or r.text[:500]}")
        return data

    def lay_ma_in(self, ds_ma_van_don: list[str], expiry_epoch_ms: Optional[int] = None) -> str:
        from datetime import datetime as _dt

        if expiry_epoch_ms is None:
            expiry_epoch_ms = int((_dt.utcnow() + timedelta(days=30)).timestamp() * 1000)
        endpoint = "/v2/order/printing-code"
        body = {"EXPIRY_TIME": expiry_epoch_ms, "ORDER_ARRAY": ds_ma_van_don}
        with self._client() as c:
            r = c.post(endpoint, json=body, headers=self._headers())
        self._log(endpoint, "POST", body, r)
        try:
            data = r.json()
        except Exception:
            raise VtpError(f"VTP trả response không phải JSON: {r.text[:500]}")
        if r.status_code != 200 or data.get("error"):
            raise VtpError(f"printing-code: {data.get('message') or r.text[:500]}")
        return data.get("message") or ""

    def link_in_nhan(self, ma_code: str, kho: str = "A6", hien_thi_cuoc: bool = True) -> str:
        type_map = {"A5": "1", "A6": "2", "A7": "100"}
        t = type_map.get(kho.upper(), "2")
        sp = "1" if hien_thi_cuoc else "0"
        return f"{settings.VTP_PRINT_BASE_URL}/DigitalizePrint/report.do?type={t}&bill={ma_code}&showPostage={sp}"
