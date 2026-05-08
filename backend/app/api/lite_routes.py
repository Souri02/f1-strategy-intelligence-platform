"""Routes for Vercel serverless (under AWS Lambda size limits).

Full ML, ingestion (FastF1), and strategy live in Docker via ``app.api.routes``.
This module avoids importing scikit-learn / xgboost so the deployment bundle stays small.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.models.schemas import (
    AvailableSeasonsResponse,
    DriverMetaResponse,
    FeatureBuildRequest,
    IngestionRequest,
    PrepareSeasonRequest,
    SeasonMetaResponse,
    StrategyOptimizeRequest,
    StrategySimulationRequest,
    TeamMetaResponse,
    TrainModelRequest,
)
from app.services.inventory import available_seasons
from app.services.metadata import load_driver_team_metadata

router = APIRouter()

ML_UNAVAILABLE_DETAIL = (
    "This Vercel deployment is metadata-only (scikit-learn/xgboost exceed serverless bundle limits). "
    "Run the full backend with Docker on your machine, or deploy the ``backend`` image elsewhere, "
    "for ingestion, model training, and strategy simulation."
)


def _raise_api_error(exc: Exception) -> None:
    if isinstance(exc, FileNotFoundError):
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if isinstance(exc, ValueError):
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "mode": "lite"}


@router.get("/data/available-seasons", response_model=AvailableSeasonsResponse)
def get_available_seasons() -> AvailableSeasonsResponse:
    seasons = available_seasons(settings.data_dir)
    return AvailableSeasonsResponse(**seasons)


@router.get("/meta/season/{season}", response_model=SeasonMetaResponse)
def get_season_meta(season: int) -> SeasonMetaResponse:
    try:
        drivers, teams = load_driver_team_metadata(settings.data_dir, season=season)
    except Exception as exc:
        _raise_api_error(exc)

    return SeasonMetaResponse(
        season=season,
        drivers=[
            DriverMetaResponse(
                code=d.code,
                full_name=d.full_name,
                constructor=d.constructor,
                wikipedia_title=d.wikipedia_title,
            )
            for d in drivers
        ],
        teams=[
            TeamMetaResponse(
                constructor_id=t.constructor_id,
                constructor_name=t.constructor_name,
                wikipedia_title=t.wikipedia_title,
            )
            for t in teams
        ],
    )


@router.post("/ingestion/season")
def ingest_season_unavailable(_: IngestionRequest) -> None:
    raise HTTPException(status_code=503, detail=ML_UNAVAILABLE_DETAIL)


@router.post("/features/lap")
def build_lap_features_unavailable(_: FeatureBuildRequest) -> None:
    raise HTTPException(status_code=503, detail=ML_UNAVAILABLE_DETAIL)


@router.post("/models/lap-time/train")
def train_unavailable(_: TrainModelRequest) -> None:
    raise HTTPException(status_code=503, detail=ML_UNAVAILABLE_DETAIL)


@router.post("/strategy/simulate")
def simulate_unavailable(_: StrategySimulationRequest) -> None:
    raise HTTPException(status_code=503, detail=ML_UNAVAILABLE_DETAIL)


@router.post("/strategy/optimize")
def optimize_unavailable(_: StrategyOptimizeRequest) -> None:
    raise HTTPException(status_code=503, detail=ML_UNAVAILABLE_DETAIL)


@router.post("/season/prepare")
def prepare_unavailable(_: PrepareSeasonRequest) -> None:
    raise HTTPException(status_code=503, detail=ML_UNAVAILABLE_DETAIL)
