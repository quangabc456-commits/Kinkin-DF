from __future__ import annotations

import time

import httpx
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.core.db import get_session
from app.models import DiaDanhHuyen, DiaDanhTinh, DiaDanhXa


CAT_BASE = "https://partner.viettelpost.vn"


def fetch_tinh(client: httpx.Client) -> list[dict]:
    r = client.get(f"{CAT_BASE}/v2/categories/listProvinceById", params={"provinceId": -1})
    r.raise_for_status()
    return r.json()


def fetch_huyen(client: httpx.Client) -> list[dict]:
    r = client.get(f"{CAT_BASE}/v2/categories/listDistrict", params={"provinceId": -1})
    r.raise_for_status()
    return r.json()


def fetch_xa(client: httpx.Client, district_id: int) -> list[dict]:
    r = client.get(f"{CAT_BASE}/v2/categories/listWards", params={"districtId": district_id})
    r.raise_for_status()
    return r.json()


def upsert_dia_danh(verbose: bool = True) -> dict:
    with httpx.Client(timeout=30.0) as client:
        if verbose:
            print("Đang tải danh sách tỉnh...")
        ds_tinh = fetch_tinh(client)
        if verbose:
            print(f"  {len(ds_tinh)} tỉnh")
            print("Đang tải danh sách huyện...")
        ds_huyen = fetch_huyen(client)
        if verbose:
            print(f"  {len(ds_huyen)} huyện")

        with get_session() as session:
            for t in ds_tinh:
                stmt = pg_insert(DiaDanhTinh).values(
                    id=t["PROVINCE_ID"],
                    ma_tinh=t.get("PROVINCE_CODE"),
                    ten_tinh=t["PROVINCE_NAME"],
                )
                stmt = stmt.on_conflict_do_update(
                    index_elements=["id"],
                    set_={"ma_tinh": stmt.excluded.ma_tinh, "ten_tinh": stmt.excluded.ten_tinh},
                )
                session.execute(stmt)

            for h in ds_huyen:
                is_new_addr = (h.get("DISTRICT_VALUE") or "").upper() == "NEW"
                stmt = pg_insert(DiaDanhHuyen).values(
                    id=h["DISTRICT_ID"],
                    tinh_id=h["PROVINCE_ID"],
                    ma_huyen=h.get("DISTRICT_VALUE"),
                    ten_huyen=h["DISTRICT_NAME"],
                    la_dia_chi_moi=is_new_addr,
                )
                stmt = stmt.on_conflict_do_update(
                    index_elements=["id"],
                    set_={
                        "tinh_id": stmt.excluded.tinh_id,
                        "ma_huyen": stmt.excluded.ma_huyen,
                        "ten_huyen": stmt.excluded.ten_huyen,
                        "la_dia_chi_moi": stmt.excluded.la_dia_chi_moi,
                    },
                )
                session.execute(stmt)

        if verbose:
            print("Đang tải xã/phường theo từng huyện (chậm, ~5-10 phút)...")
        total_xa = 0
        for i, h in enumerate(ds_huyen, 1):
            district_id = h["DISTRICT_ID"]
            try:
                ds_xa = fetch_xa(client, district_id)
            except Exception as e:
                if verbose:
                    print(f"  [{i}/{len(ds_huyen)}] huyện {district_id} lỗi: {e}")
                continue

            with get_session() as session:
                for x in ds_xa:
                    stmt = pg_insert(DiaDanhXa).values(
                        id=x["WARDS_ID"],
                        huyen_id=district_id,
                        ten_xa=x["WARDS_NAME"],
                    )
                    stmt = stmt.on_conflict_do_update(
                        index_elements=["id"],
                        set_={"huyen_id": stmt.excluded.huyen_id, "ten_xa": stmt.excluded.ten_xa},
                    )
                    session.execute(stmt)
                total_xa += len(ds_xa)

            if verbose and i % 50 == 0:
                print(f"  [{i}/{len(ds_huyen)}] đã xử lý, tổng xã: {total_xa}")
            time.sleep(0.05)

        return {"tinh": len(ds_tinh), "huyen": len(ds_huyen), "xa": total_xa}
