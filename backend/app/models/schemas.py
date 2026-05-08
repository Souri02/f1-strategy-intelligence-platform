from pydantic import BaseModel, Field


class IngestionRequest(BaseModel):
    season: int = Field(default=2024, ge=2018, le=2100)
    include_telemetry: bool = Field(default=False)


class IngestionResponse(BaseModel):
    season: int
    schedule_rows: int
    results_rows: int
    message: str


class FeatureBuildRequest(BaseModel):
    season: int = Field(default=2024, ge=2018, le=2100)


class FeatureBuildResponse(BaseModel):
    season: int
    rows: int
    output_path: str
    message: str


class TrainModelRequest(BaseModel):
    season: int = Field(default=2024, ge=2018, le=2100)
    use_gpu: bool = False


class TrainModelResponse(BaseModel):
    season: int
    model_path: str
    metrics_path: str
    rmse: float
    mae: float
    used_gpu: bool
    message: str


class StrategySimulationRequest(BaseModel):
    season: int = Field(default=2024, ge=2018, le=2100)
    round: int = Field(default=1, ge=1, le=30)
    driver: str = Field(default="VER", min_length=2, max_length=3)
    baseline_pit_lap: int = Field(default=20, ge=2, le=200)
    counterfactual_pit_lap: int = Field(default=24, ge=2, le=200)
    counterfactual_compound: str = Field(default="MEDIUM", min_length=3, max_length=16)


class StrategySimulationResponse(BaseModel):
    season: int
    round: int
    driver: str
    baseline_pit_lap: int
    counterfactual_pit_lap: int
    baseline_estimated_time_seconds: float
    counterfactual_estimated_time_seconds: float
    delta_seconds: float
    delta_confidence_low_seconds: float
    delta_confidence_high_seconds: float
    pit_stop_loss_seconds: float
    estimated_position_gain: int
    recommended_pit_lap: int
    feasible_pit_window_start: int
    feasible_pit_window_end: int
    constraints_applied: list[str]
    message: str


class StrategyOptimizeRequest(BaseModel):
    season: int = Field(default=2024, ge=2018, le=2100)
    round: int = Field(default=1, ge=1, le=30)
    driver: str = Field(default="VER", min_length=2, max_length=3)
    baseline_pit_lap: int = Field(default=20, ge=2, le=200)
    monte_carlo_samples: int = Field(default=200, ge=50, le=2000)


class StrategyCandidate(BaseModel):
    strategy_label: str
    pit_laps: list[int]
    compounds: list[str]
    estimated_time_seconds: float
    uncertainty_seconds: float
    position_gain_vs_baseline: int


class StrategyOptimizeResponse(BaseModel):
    season: int
    round: int
    driver: str
    baseline_estimated_time_seconds: float
    best_strategy: StrategyCandidate
    top_candidates: list[StrategyCandidate]
    explainability: dict[str, float]
    message: str


class AvailableSeasonsResponse(BaseModel):
    raw_laps: list[int]
    features: list[int]
    models: list[int]


class PrepareSeasonRequest(BaseModel):
    season: int = Field(default=2024, ge=2018, le=2100)
    use_gpu: bool = True


class PrepareSeasonResponse(BaseModel):
    season: int
    ingested: bool
    features_built: bool
    model_trained: bool
    message: str


class DriverMetaResponse(BaseModel):
    code: str
    full_name: str | None = None
    constructor: str | None = None
    wikipedia_title: str | None = None


class TeamMetaResponse(BaseModel):
    constructor_id: str | None = None
    constructor_name: str | None = None
    wikipedia_title: str | None = None


class SeasonMetaResponse(BaseModel):
    season: int
    drivers: list[DriverMetaResponse]
    teams: list[TeamMetaResponse]
