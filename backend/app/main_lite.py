from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.lite_routes import router as lite_router
from app.config import settings

app = FastAPI(
    title=f"{settings.project_name} (metadata API)",
    version="0.1.0",
    description="Lite serverless build for Vercel: health, season inventory, driver/team metadata. No ML.",
)

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
        "mode": "lite",
        "message": "API lives under /api/v1. Open /docs for Swagger.",
        "health": "/api/v1/health",
        "docs": "/docs",
    }


app.include_router(lite_router, prefix="/api/v1", tags=["f1"])
