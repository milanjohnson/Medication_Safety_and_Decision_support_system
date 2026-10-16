# SOURCE: NOT IN PAPERS. Standalone app for local use; the team can instead include `router`.
"""Run from the aakaash folder:  python -m uvicorn api.app:app --port 8000"""
import logging
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .router import router
from .services import datasets

log = logging.getLogger("uvicorn.error")


def _warm_ddi_cache() -> None:
    """Parsing the DDI corpus takes a few seconds; do it in the background at startup so the
    first dashboard request does not wait. Failures are logged, not hidden."""
    try:
        datasets.load_ddi(get_settings())
    except Exception:  # noqa: BLE001
        log.exception("DDI cache warm-up failed")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    threading.Thread(target=_warm_ddi_cache, daemon=True).start()
    yield


app = FastAPI(title="Medication safety: subareas A and B",
              description="Research prototype. Decision support only. Not medical advice.",
              lifespan=lifespan)
app.add_middleware(  # the Vite dev server
    CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST"], allow_headers=["*"])
app.include_router(router)
