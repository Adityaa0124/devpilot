from fastapi import APIRouter

from app.api.health import router as health_router
from app.api.run import router as run_router
from app.api.run_stream import router as run_stream_router
from app.api.runs import router as runs_router

router = APIRouter()

router.include_router(health_router)
router.include_router(run_router)
router.include_router(run_stream_router)
router.include_router(runs_router)
