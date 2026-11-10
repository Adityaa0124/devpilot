import warnings
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from pathlib import Path
from fastapi.responses import FileResponse

from app.api.router import router
import uvicorn

warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])

app = FastAPI(
    title="DevPilot — Multi-Agent AI Software Engineering System",
    description="Autonomous multi-agent engineering assistant that plans, develops, secures, tests, and reviews code.",
    version="1.0.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_INDEX = Path(__file__).resolve().parent.parent / "frontend" / "index.html"


@app.get("/", include_in_schema=False)
def serve_index():
    """Serves the DevPilot web dashboard directly at the root URL."""
    if FRONTEND_INDEX.exists():
        return FileResponse(FRONTEND_INDEX)
    return {"message": "DevPilot API is running. Visit /docs for OpenAPI documentation."}


app.include_router(router, prefix="/api/v1")


if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", "8001"))
    host = os.getenv("HOST", "127.0.0.1")
    uvicorn.run(
        "app.server:app",
        host=host,
        port=port,
        reload=True,
        reload_dirs=["app"],  # watch only app/ — ignore workspace/ to avoid unnecessary reloads
    )
