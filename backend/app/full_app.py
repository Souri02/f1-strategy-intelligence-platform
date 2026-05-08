"""Full FastAPI application (Docker / local): all routes including ML and ingestion."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config import settings

app = FastAPI(title=settings.project_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", include_in_schema=True)
def root() -> dict[str, str]:
    """Avoid bare 404 when opening the deployment root URL in a browser."""
    return {
        "service": settings.project_name,
        "mode": "full",
        "message": "API under /api/v1. Open /docs for Swagger.",
        "health": "/api/v1/health",
        "docs": "/docs",
    }


app.include_router(router, prefix="/api/v1", tags=["f1"])
