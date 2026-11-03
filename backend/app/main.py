import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import StaleDataError
from .api import router
from . import operations, ai, reference_packs, ai_report
from .config import settings
from .database import session_factory

logger = logging.getLogger("labquality")
app = FastAPI(title="LabQuality Copilot", version="0.2.0", docs_url="/api/docs", openapi_url="/api/openapi.json")


@app.middleware("http")
async def protections(request: Request, call_next):
    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        origin = request.headers.get("origin")
        if origin and origin not in settings().allowed_origins.split(","):
            return JSONResponse({"detail": "Origem não autorizada."}, status_code=403)
        if request.headers.get("x-labquality-client") != "web":
            return JSONResponse({"detail": "Cabeçalho X-LabQuality-Client: web obrigatório."}, status_code=403)
        try:
            declared = int(request.headers.get("content-length", "0"))
        except ValueError:
            return JSONResponse({"detail": "Tamanho inválido."}, status_code=400)
        if declared > 12_000_000:
            return JSONResponse({"detail": "Pedido demasiado grande."}, status_code=413)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Cache-Control"] = "no-store"
    response.headers["Referrer-Policy"] = "same-origin"
    return response


@app.exception_handler(IntegrityError)
async def integrity_error(request, exc):
    return JSONResponse({"detail": "Já existe um registo com esta identidade ou uma relação é inválida. Actualize os dados."}, status_code=409)


@app.exception_handler(StaleDataError)
async def stale_error(request, exc):
    return JSONResponse({"detail": "Outro utilizador alterou o registo. Actualize a página."}, status_code=409)


@app.get("/api/health")
def health():
    try:
        with session_factory()() as db:
            db.execute(text("SELECT 1"))
            db.execute(text("SELECT version_num FROM alembic_version"))
        return {"status": "ok", "version": "0.2.0"}
    except Exception:
        return JSONResponse({"status": "unavailable", "detail": "Base de dados ou migrations indisponíveis."}, status_code=503)


app.include_router(router)
