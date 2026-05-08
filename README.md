# F1 Strategy Intelligence Platform

An end-to-end AI and analytics project for Formula 1 strategy intelligence.  
This repository is intentionally designed as a long-horizon, production-style portfolio project with backend, frontend, and ML/data pipelines.

## Why this project matters

This project demonstrates:
- data ingestion from multiple sources (FastF1 + race results APIs),
- API engineering with FastAPI,
- product UI with Next.js,
- path to advanced ML use cases (counterfactual strategy simulation, pit-window optimization, race outcome modeling),
- deployable architecture with Docker.

## Portfolio narrative (recruiters & interviews)

See **[docs/portfolio.md](docs/portfolio.md)** for elevator pitch, talking points, architecture diagram, and benchmark table.  
Technical delivery history: **[docs/phase_report.md](docs/phase_report.md)** · System diagram: **[docs/architecture.md](docs/architecture.md)**.

## Dependency guarantee (no missing packages)

Everything needed for a **full local/Docker backend** (including FastF1 ingestion) is listed in **`backend/requirements.full.txt`**. For **Vercel’s free serverless backend**, dependencies are the flat list in **`backend/requirements.txt`** (kept in sync with **`backend/requirements.vercel.txt`**; no FastF1 — run ingestion via Docker locally). Everything for the **frontend** is in **`frontend/package.json`** with a lockfile **`frontend/package-lock.json`** (reproducible installs: `npm ci`).

After installing, verify Python:

```bash
# From repository root (with venv active and backend deps installed):
python scripts/verify_environment.py
```

This script imports every third-party module used by the app, loads the FastAPI app, and runs **`pip check`** so **broken or conflicting dependencies** fail fast.

In Docker, the same check applies:

```bash
docker compose run --rm backend python scripts/verify_environment.py
```

## Current scope (Phases 1–4 + polish)

- Monorepo scaffold with backend, frontend, pipelines, ML, docs, and infra folders.
- FastAPI backend with health and ingestion endpoints.
- Data ingestion for:
  - season event schedule from FastF1,
  - season race results from Jolpica/Ergast-compatible endpoints.
- Data storage in Parquet under `data/raw` and `data/processed`.
- Phase 2 telemetry-style lap ingestion from FastF1 race sessions.
- Phase 2 lap feature engineering pipeline for ML-ready training data.
- Phase 2 baseline next-lap-time model training with optional GPU (`use_gpu`).
- Phase 3 counterfactual strategy simulator API and frontend controls.
- Phase 4 multi-stop strategy optimization, Monte Carlo uncertainty, explainability signals.
- Next.js frontend with strategy simulator and optimizer actions.
- Dockerfiles and docker-compose for local orchestration (optional NVIDIA GPU for training).

## Planned advanced roadmap

1. Stint-aware tire degradation models tied to compound and track.
2. Safety car / VSC probability integrated into strategy scores.
3. Experiment tracking and model registry (MLflow or similar).
4. CI/CD (lint, tests, `verify_environment.py` on PR).
5. Cloud deployment reference (single region, managed DB optional).

## Repository structure

- `backend/` - FastAPI service and ingestion logic.
- `frontend/` - Next.js web app.
- `pipelines/` - Batch ingestion/processing scripts.
- `ml/` - Feature and model modules (upcoming).
- `infra/` - Infrastructure-related assets.
- `docs/` - Design docs, portfolio narrative, phased report.
- `scripts/` - Environment verification (`verify_environment.py`).
- `data/` - Local data lake (`raw`, `processed`).

## Dataset plan

Primary datasets:
- **FastF1**: event schedule, session/lap telemetry ecosystem.
- **Jolpica/Ergast-compatible API**: race result history.

Planned enrichments:
- weather history per circuit and race timestamp,
- circuit metadata (layout and track profile),
- optional event sentiment/news signals.

## Prerequisites

- Python 3.11+
- Node.js 20+
- Docker Desktop (recommended for simple startup)

## Environment setup

1. Copy **`.env.example`** in the project root to **`.env`** (used by Docker Compose).
2. For **local Python** with `cd backend` (venv + uvicorn), copy **`backend/.env.example`** to **`backend/.env`** so `F1_DATA_DIR` points at the repo **`data/`** folder (`../data` from `backend/`). If you skip this, data files are created under `backend/data/` instead.

## End-to-end: run everything from zero

Do this once before demos or interviews.

### Option A — Docker (simplest)

1. Install [Docker Desktop](https://www.docker.com/products/docker-desktop/) (with WSL2 on Windows if prompted).
2. Clone or copy this repository and open a terminal at the **project root** (`F1 Project/`).
3. Copy `.env.example` → `.env` (defaults are fine).
4. Verify backend dependencies inside the image:
   ```bash
   docker compose run --rm backend python scripts/verify_environment.py
   ```
5. Start stack:
   ```bash
   docker compose up --build -d
   ```
6. Open **http://localhost:3000** (frontend) and **http://localhost:8000/docs** (API docs).
7. **First-time data + model** (from host, with backend up):
   - `POST /api/v1/ingestion/season` with `{"season":2024,"include_telemetry":true}` (takes several minutes),
   - then `POST /api/v1/features/lap` with `{"season":2024}`,
   - then `POST /api/v1/models/lap-time/train` with `{"season":2024,"use_gpu":true}` (GPU optional),
   - then try **Strategy simulate** / **Optimize** on the home page.

Data persists under **`data/`** on your machine via the volume mount.

### Option B — Local Python + Node (no Docker)

1. **Python backend**
   - `cd backend`
   - `python -m venv .venv` then activate (Windows: `.venv\Scripts\activate`; macOS/Linux: `source .venv/bin/activate`).
   - Copy **`backend/.env.example`** → **`backend/.env`** (writes datasets to **`../data/`** at repo root).
   - `pip install -r requirements.full.txt`
   - From **repository root** (venv still active): `python scripts/verify_environment.py`
   - `cd backend` and start API: `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`

2. **Data pipeline** (second terminal, venv active, **`cd backend`**):
   ```bash
   python run_ingestion.py --season 2024 --include-telemetry
   python run_build_features.py --season 2024
   python run_train_model.py --season 2024 --use-gpu
   ```

3. **Frontend** (third terminal):
   ```bash
   cd frontend
   npm ci
   npm run dev
   ```
   If the UI shows “backend not reachable”, set **`NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`** (e.g. in `frontend/.env.local`).

4. Open **http://localhost:3000**.

## Local run (without Docker)

The steps below are the same building blocks as **Option B**. All `data/...` paths below assume **`backend/.env`** is configured so `F1_DATA_DIR` resolves to the repo **`data/`** folder.

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
copy .env.example .env
pip install -r requirements.full.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

On macOS/Linux use `cp .env.example .env` instead of `copy`.

Backend URLs:
- API root health: `http://localhost:8000/api/v1/health`
- Swagger docs: `http://localhost:8000/docs`

### Run ingestion manually

```bash
cd backend
python run_ingestion.py --season 2024
```

Expected output files:
- `data/raw/schedule_2024.parquet`
- `data/raw/results_2024.parquet`

### Run telemetry/lap ingestion (Phase 2)

```bash
cd backend
python run_ingestion.py --season 2024 --include-telemetry
```

Expected output file:
- `data/raw/laps_2024.parquet`

### Build lap features (Phase 2)

```bash
cd backend
python run_build_features.py --season 2024
```

Expected output file:
- `data/processed/lap_features_2024.parquet`

### Train baseline model (Phase 2)

```bash
cd backend
python run_train_model.py --season 2024 --use-gpu
```

Expected output files:
- `data/processed/models/lap_time_baseline_xgb_2024.joblib`
- `data/processed/models/lap_time_baseline_xgb_2024_metrics.json`

### Frontend

```bash
cd frontend
npm ci
npm run dev
```

Use **`npm ci`** when `package-lock.json` is present for repeatable installs; use `npm install` only when adding dependencies.

Frontend URL:
- `http://localhost:3000`

## Docker run

```bash
docker compose up --build
```

Services:
- backend on `http://localhost:8000`
- frontend on `http://localhost:3000`

### Docker GPU setup (RTX 3080)

To allow model training on your GPU from Docker:

1. Ensure Docker Desktop has WSL2 backend enabled.
2. Ensure NVIDIA GPU drivers are installed on Windows.
3. Confirm host GPU visibility:

```bash
nvidia-smi
```

4. Start services with compose (this repo already includes **NVIDIA GPU device reservations** for the backend service when your Docker stack supports it):

```bash
docker compose up --build -d
```

5. Validate GPU visibility inside backend container:

```bash
docker compose exec backend nvidia-smi
```

If the command above fails, Docker runtime cannot access the GPU yet; training will still run on CPU with automatic fallback.

## API endpoints

- `GET /api/v1/health`
- `POST /api/v1/ingestion/season`
- `POST /api/v1/features/lap`
- `POST /api/v1/models/lap-time/train`
- `POST /api/v1/strategy/simulate`
- `POST /api/v1/strategy/optimize`

Sample ingestion payload:

```json
{
  "season": 2024,
  "include_telemetry": false
}
```

Sample model train payload:

```json
{
  "season": 2024,
  "use_gpu": true
}
```

Sample strategy simulation payload:

```json
{
  "season": 2024,
  "round": 1,
  "driver": "VER",
  "baseline_pit_lap": 20,
  "counterfactual_pit_lap": 24,
  "counterfactual_compound": "MEDIUM"
}
```

Simulation output includes:
- baseline and counterfactual estimated race time,
- delta with 95% uncertainty bounds,
- pit-stop loss assumption used in calculation,
- feasible pit window based on stint constraints,
- recommended pit lap and estimated position impact.

Strategy optimization output includes:
- best one-stop/two-stop plan from candidate search,
- Monte Carlo uncertainty on predicted race time,
- top candidate strategies,
- feature-sensitivity explainability signals.

Sample strategy optimize payload:

```json
{
  "season": 2024,
  "round": 1,
  "driver": "VER",
  "baseline_pit_lap": 20,
  "monte_carlo_samples": 200
}
```

## Troubleshooting

- **FastF1 fetch errors or timeouts**  
  Retry once; if network is unstable, test connectivity first.

- **Race results endpoint unavailable**  
  The code already attempts both Jolpica and Ergast-compatible fallback URLs.

- **`ModuleNotFoundError` when running scripts**  
  Run from `backend/` using `python run_*.py` scripts so package paths resolve correctly.

- **GPU flag is enabled but CUDA is unavailable**  
  Training automatically falls back to CPU and continues (`used_gpu` will be `false` in API response).

- **Docker container does not see your GPU**  
  By default, Docker runs CPU-only unless GPU runtime is explicitly configured.

- **Frontend cannot reach backend**  
  Ensure backend is running on port `8000`, and check `NEXT_PUBLIC_API_BASE_URL`.

- **Docker compose startup fails**  
  Rebuild with `docker compose build --no-cache` and retry.

## How to contribute and avoid mistakes

- Keep data exploration in `notebooks/`.
- Move reusable logic into Python modules under `backend/app` or `ml/`.
- Add tests for new endpoints and model logic in `backend/tests`.
- Document each phase update in `docs/`.

## Recommended notebook usage

Use notebooks for:
- EDA,
- quick feature experiments,
- visualization drafts.

Use Python modules for:
- ingestion pipelines,
- model training code,
- API integration,
- reusable business logic.

This hybrid workflow gives both research flexibility and production reliability.
