from __future__ import annotations

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.controllers.cau_hinh_controller import router as router_cau_hinh
from app.controllers.kinkin_controller import router as router_kinkin
from app.controllers.pgh_controller import router as router_pgh
from app.controllers.webhook_controller import router as router_webhook
from app.core.config import settings


app = FastAPI(title="Kinkin - Quản lý PGH ViettelPost")

app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(router_webhook)
app.include_router(router_cau_hinh)
app.include_router(router_kinkin)
app.include_router(router_pgh)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host=settings.APP_HOST, port=settings.APP_PORT, reload=True)
