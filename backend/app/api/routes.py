from fastapi import APIRouter, HTTPException

from app.config import settings
from app.models.schemas import (
    AvailableSeasonsResponse,
    DriverMetaResponse,
    FeatureBuildRequest,
    FeatureBuildResponse,
    IngestionRequest,
    IngestionResponse,
    PrepareSeasonRequest,
    PrepareSeasonResponse,
    SeasonMetaResponse,
    StrategyCandidate,
    StrategyOptimizeRequest,
    StrategyOptimizeResponse,
    StrategySimulationRequest,
    StrategySimulationResponse,
    TeamMetaResponse,
    TrainModelRequest,
    TrainModelResponse,
)
from app.services.feature_engineering import build_lap_feature_table
from app.services.ingestion import ingest_season_data
from app.services.inventory import available_seasons
from app.services.metadata import load_driver_team_metadata
from app.services.model_training import train_lap_time_baseline
from app.services.strategy_simulation import optimize_strategy_plan, run_strategy_counterfactual

router = APIRouter()


def _raise_api_error(exc: Exception) -> None:
    if isinstance(exc, FileNotFoundError):
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if isinstance(exc, ValueError):
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


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


@router.post("/ingestion/season", response_model=IngestionResponse)
def ingest_season(payload: IngestionRequest) -> IngestionResponse:
    try:
        stats = ingest_season_data(
            data_dir=settings.data_dir,
            season=payload.season,
            include_telemetry=payload.include_telemetry,
        )
    except Exception as exc:
        _raise_api_error(exc)

    return IngestionResponse(
        season=payload.season,
        schedule_rows=stats["schedule_rows"],
        results_rows=stats["results_rows"],
        message="Season ingestion completed successfully.",
    )


@router.post("/features/lap", response_model=FeatureBuildResponse)
def build_lap_features(payload: FeatureBuildRequest) -> FeatureBuildResponse:
    try:
        feature_df, output_path = build_lap_feature_table(
            data_dir=settings.data_dir,
            season=payload.season,
        )
    except Exception as exc:
        _raise_api_error(exc)

    return FeatureBuildResponse(
        season=payload.season,
        rows=len(feature_df),
        output_path=str(output_path),
        message="Lap feature table built successfully.",
    )


@router.post("/models/lap-time/train", response_model=TrainModelResponse)
def train_lap_time_model(payload: TrainModelRequest) -> TrainModelResponse:
    try:
        stats = train_lap_time_baseline(
            data_dir=settings.data_dir,
            season=payload.season,
            use_gpu=payload.use_gpu,
        )
    except Exception as exc:
        _raise_api_error(exc)

    return TrainModelResponse(
        season=payload.season,
        model_path=stats["model_path"],
        metrics_path=stats["metrics_path"],
        rmse=stats["rmse"],
        mae=stats["mae"],
        used_gpu=stats["used_gpu"],
        message="Baseline lap-time model training completed.",
    )


@router.post("/strategy/simulate", response_model=StrategySimulationResponse)
def simulate_strategy(payload: StrategySimulationRequest) -> StrategySimulationResponse:
    try:
        stats = run_strategy_counterfactual(
            data_dir=settings.data_dir,
            season=payload.season,
            round_no=payload.round,
            driver=payload.driver,
            baseline_pit_lap=payload.baseline_pit_lap,
            counterfactual_pit_lap=payload.counterfactual_pit_lap,
            counterfactual_compound=payload.counterfactual_compound,
        )
    except Exception as exc:
        _raise_api_error(exc)

    return StrategySimulationResponse(
        season=stats["season"],
        round=stats["round"],
        driver=stats["driver"],
        baseline_pit_lap=stats["baseline_pit_lap"],
        counterfactual_pit_lap=stats["counterfactual_pit_lap"],
        baseline_estimated_time_seconds=stats["baseline_estimated_time_seconds"],
        counterfactual_estimated_time_seconds=stats["counterfactual_estimated_time_seconds"],
        delta_seconds=stats["delta_seconds"],
        delta_confidence_low_seconds=stats["delta_confidence_low_seconds"],
        delta_confidence_high_seconds=stats["delta_confidence_high_seconds"],
        pit_stop_loss_seconds=stats["pit_stop_loss_seconds"],
        estimated_position_gain=stats["estimated_position_gain"],
        recommended_pit_lap=stats["recommended_pit_lap"],
        feasible_pit_window_start=stats["feasible_pit_window_start"],
        feasible_pit_window_end=stats["feasible_pit_window_end"],
        constraints_applied=stats["constraints_applied"],
        message="Counterfactual strategy simulation completed.",
    )


@router.post("/strategy/optimize", response_model=StrategyOptimizeResponse)
def optimize_strategy(payload: StrategyOptimizeRequest) -> StrategyOptimizeResponse:
    try:
        stats = optimize_strategy_plan(
            data_dir=settings.data_dir,
            season=payload.season,
            round_no=payload.round,
            driver=payload.driver,
            baseline_pit_lap=payload.baseline_pit_lap,
            monte_carlo_samples=payload.monte_carlo_samples,
        )
    except Exception as exc:
        _raise_api_error(exc)

    best = StrategyCandidate(**stats["best_strategy"])
    top = [StrategyCandidate(**item) for item in stats["top_candidates"]]
    return StrategyOptimizeResponse(
        season=stats["season"],
        round=stats["round"],
        driver=stats["driver"],
        baseline_estimated_time_seconds=stats["baseline_estimated_time_seconds"],
        best_strategy=best,
        top_candidates=top,
        explainability=stats["explainability"],
        message="Strategy optimization completed.",
    )


@router.post("/season/prepare", response_model=PrepareSeasonResponse)
def prepare_season(payload: PrepareSeasonRequest) -> PrepareSeasonResponse:
    season = payload.season
    try:
        ingest_season_data(settings.data_dir, season=season, include_telemetry=True)
        feature_df, _ = build_lap_feature_table(settings.data_dir, season=season)
        model_trained = True
        try:
            train_lap_time_baseline(settings.data_dir, season=season, use_gpu=payload.use_gpu)
        except ValueError as exc:
            # e.g. too few rows (common for incomplete seasons like early 2025)
            model_trained = False
            return PrepareSeasonResponse(
                season=season,
                ingested=True,
                features_built=len(feature_df) > 0,
                model_trained=False,
                message=f"Prepared season {season} (model not trained): {exc}",
            )
    except Exception as exc:
        _raise_api_error(exc)

    return PrepareSeasonResponse(
        season=season,
        ingested=True,
        features_built=True,
        model_trained=model_trained,
        message=f"Prepared season {season} successfully.",
    )