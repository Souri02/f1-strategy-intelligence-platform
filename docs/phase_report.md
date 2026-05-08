# F1 Strategy Intelligence Platform: Detailed Progress Report

## Executive Summary

This report documents completed implementation across Phase 1, Phase 2, and Phase 3.1.
The project now includes an end-to-end stack with:
- data ingestion and storage,
- feature engineering,
- GPU-enabled model training,
- counterfactual strategy simulation API,
- interactive frontend for scenario testing.

## Phase 1: Platform Foundation

### Implemented
- Monorepo structure for backend, frontend, pipelines, ML, docs, and infra.
- FastAPI backend with health and ingestion endpoints.
- Data ingestion from:
  - FastF1 schedule data,
  - Jolpica/Ergast-compatible race results API.
- Raw data persisted as parquet in `data/raw`.
- Next.js frontend baseline connectivity page.
- Dockerized backend + frontend via compose.

### Key fixes applied
- FastF1 cache directory creation added before cache enable.
- README runbook and troubleshooting guidance added for reproducibility.

## Phase 2: ML Pipeline and Training

### Implemented
- Lap-level telemetry-style race ingestion from FastF1 (`include_telemetry=true`).
- Feature engineering pipeline output to `data/processed/lap_features_<season>.parquet`.
- XGBoost baseline model for next-lap-time prediction.
- API endpoint for training with optional GPU flag.
- Runner scripts for ingestion, feature build, and model training.

### Model artifacts
- Trained model: `data/processed/models/lap_time_baseline_xgb_2024.joblib`
- Metrics: `data/processed/models/lap_time_baseline_xgb_2024_metrics.json`

### Reliability improvements
- Dtype normalization for merge keys (`season`, `round`).
- RMSE computation compatibility fix for sklearn version differences.
- GPU availability detection added (`nvidia-smi`) with robust CPU fallback.

## Phase 3: Counterfactual Simulation

### Implemented
- Backend strategy simulation service:
  - baseline vs counterfactual pit-lap comparison,
  - model-based race-time estimation.
- New API endpoint: `POST /api/v1/strategy/simulate`.
- Frontend scenario controls and result panel for interactive experimentation.

## Phase 3.1: Simulation Quality Upgrade

### Implemented upgrades
- **Pit-stop loss modeling**:
  - explicit pit-in and pit-out penalties derived from race pace.
- **Race constraints**:
  - pit lap constrained to feasible stint window.
  - minimum stint length assumptions enforced.
- **Uncertainty bounds**:
  - delta confidence interval (95%) computed from race variability and strategy shift magnitude.
- **Transparent outputs**:
  - feasible pit window returned,
  - applied constraints listed,
  - pit-loss assumption exposed in response.

### API response now includes
- `delta_confidence_low_seconds`
- `delta_confidence_high_seconds`
- `pit_stop_loss_seconds`
- `feasible_pit_window_start`
- `feasible_pit_window_end`
- `constraints_applied`

## Frontend Enhancements Completed

- Added `StrategySimulator` client component with:
  - configurable race/driver/pit scenario inputs,
  - simulation trigger button,
  - detailed output visualization including uncertainty and constraints.
- Updated dashboard milestone section to reflect delivered phases.

## Validation and Verification Summary

### Backend
- Python compilation checks passed after each major change.
- Endpoint smoke tests executed:
  - health,
  - season ingestion,
  - feature build,
  - model training (CPU/GPU paths),
  - strategy simulation.

### Frontend
- Next.js production build passed after Phase 3 integration.
- Type checks and lints showed no issues in modified files.

### Docker and GPU
- Docker backend configured for NVIDIA runtime.
- `docker compose exec backend nvidia-smi` confirms container GPU visibility.
- Training with `use_gpu=true` confirmed active GPU path in metrics when runtime is available.

## Known Limitations (Current State)

- Strategy simulation currently models one-stop counterfactual changes only.
- Position gain estimation uses a heuristic conversion from time delta.
- No explicit safety-car probability model yet.
- No Monte Carlo race-level uncertainty propagation yet.

## Next Recommended Milestones

1. Multi-stop strategy optimizer with integer programming or dynamic programming.
2. Safety-car and VSC probability model integration.
3. Track-specific pit-loss profiles from empirical historical data.
4. Explainability endpoint with feature contributions for each simulation.
5. Experiment tracking and model version registry.

## Hiring Narrative Value

This project now demonstrates cross-functional engineering depth:
- data engineering,
- applied ML,
- simulation logic,
- API productization,
- frontend delivery,
- Docker and GPU-aware runtime operations.

It is suitable as a flagship portfolio project for data analyst, AI engineer, and ML engineer roles.

## Phase 4 Addendum (Implemented)

- Added strategy optimization endpoint `POST /api/v1/strategy/optimize`.
- Added candidate search across one-stop and two-stop plans.
- Added Monte Carlo uncertainty scoring for candidate race-time estimates.
- Added explainability signals from scenario feature perturbation sensitivity.
- Added frontend optimization trigger and result rendering for best strategy output.
