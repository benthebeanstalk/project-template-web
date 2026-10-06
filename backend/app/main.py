from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings

app = FastAPI(title="app")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


# Mount last so /api routes win. In production the Docker image holds the built frontend here.
if Path(settings.static_dir).is_dir():
    app.mount("/", StaticFiles(directory=settings.static_dir, html=True), name="static")
