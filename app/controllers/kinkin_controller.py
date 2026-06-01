from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.services.kinkin_lookup import lookup_code


router = APIRouter(prefix="/api/kinkin", tags=["kinkin"])


@router.get("/lookup/{code}")
def api_lookup(code: str, session: Session = Depends(get_db)) -> dict:
    """Auto-detect prefix code → trả info kết hợp local (du_lieu_sheet) + Kinkin upstream."""
    return lookup_code(session, code)
