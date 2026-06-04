from __future__ import annotations

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.controllers.cau_hinh_controller import router as router_cau_hinh
from app.controllers.kinkin_controller import router as router_kinkin
from app.controllers.pgh_cho_dien_controller import router as router_pgh_cho_dien
from app.controllers.pgh_kho_den_controller import router as router_pgh_kho_den
from app.controllers.pgh_controller import router as router_pgh
from app.controllers.webhook_controller import router as router_webhook
from app.core.config import settings


app = FastAPI(title="Kinkin - Quản lý PGH ViettelPost")

app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(router_webhook)
app.include_router(router_cau_hinh)
app.include_router(router_kinkin)
app.include_router(router_pgh_cho_dien)
app.include_router(router_pgh_kho_den)
app.include_router(router_pgh)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/env")
def health_env() -> dict[str, object]:
    """Diagnostic: confirm env vars loaded (no secrets exposed)."""
    import os

    from app.core.config import settings

    def safe(v: str | None) -> dict[str, object]:
        if not v:
            return {"set": False, "len": 0}
        return {
            "set": True,
            "len": len(v),
            "first8": v[:8],
            "last4": v[-4:] if len(v) > 4 else "",
        }

    return {
        "DATABASE_URL_settings": safe(settings.DATABASE_URL),
        "DATABASE_URL_env": safe(os.getenv("DATABASE_URL")),
        "KK_USERNAME_set": bool(settings.KK_USERNAME),
        "KK_PASSWORD_set": bool(settings.KK_PASSWORD),
        "GOOGLE_CREDS_JSON_B64_set": bool(settings.GOOGLE_CREDS_JSON_B64),
        "ENABLE_SYNC_UI": settings.ENABLE_SYNC_UI,
        "default_in_use": "localhost:5432" in settings.DATABASE_URL,
    }


if __name__ == "__main__":
    uvicorn.run("app.main:app", host=settings.APP_HOST, port=settings.APP_PORT, reload=True)
