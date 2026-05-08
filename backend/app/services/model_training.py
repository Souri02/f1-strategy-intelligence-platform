from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from xgboost import XGBRegressor


def _gpu_runtime_available() -> bool:
    nvidia_smi = shutil.which("nvidia-smi")
    if not nvidia_smi:
        return False
    try:
        result = subprocess.run(
            [nvidia_smi, "--query-gpu=name", "--format=csv,noheader"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0 and bool(result.stdout.strip())
    except Exception:
        return False


def _build_estimator(use_gpu: bool) -> tuple[XGBRegressor, bool]:
    if use_gpu:
        return (
            XGBRegressor(
                n_estimators=350,
                max_depth=8,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8,
                objective="reg:squarederror",
                tree_method="hist",
                device="cuda",
                random_state=42,
            ),
            True,
        )
    return (
        XGBRegressor(
            n_estimators=300,
            max_depth=7,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            objective="reg:squarederror",
            tree_method="hist",
            random_state=42,
        ),
        False,
    )


def train_lap_time_baseline(data_dir: Path, season: int, use_gpu: bool) -> dict[str, Any]:
    features_path = data_dir / "processed" / f"lap_features_{season}.parquet"
    if not features_path.exists():
        raise FileNotFoundError(
            f"{features_path} not found. Build lap features before training."
        )

    df = pd.read_parquet(features_path)
    target_col = "next_lap_time_seconds"
    df = df.dropna(subset=[target_col])
    if len(df) < 200:
        raise ValueError("Not enough feature rows for stable baseline training.")

    feature_cols = [
        "round",
        "driver",
        "team",
        "lap_number",
        "stint",
        "compound",
        "tire_life",
        "position",
        "grid_position",
        "final_position",
        "race_points",
        "is_pit_in_lap",
        "is_pit_out_lap",
        "is_safety_car_like",
        "lap_time_seconds",
    ]
    X = df[feature_cols].copy()
    y = df[target_col].copy()

    categorical_cols = ["driver", "team", "compound"]
    numeric_cols = [col for col in feature_cols if col not in categorical_cols]

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", SimpleImputer(strategy="median"), numeric_cols),
            (
                "cat",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("onehot", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                categorical_cols,
            ),
        ]
    )

    gpu_enabled = use_gpu and _gpu_runtime_available()
    estimator, used_gpu = _build_estimator(use_gpu=gpu_enabled)
    model_pipeline = Pipeline(
        steps=[
            ("preprocess", preprocessor),
            ("model", estimator),
        ]
    )

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    try:
        model_pipeline.fit(X_train, y_train)
    except Exception:
        # If GPU mode fails (e.g., CUDA runtime mismatch), retry on CPU.
        if use_gpu:
            estimator, used_gpu = _build_estimator(use_gpu=False)
            model_pipeline = Pipeline(
                steps=[
                    ("preprocess", preprocessor),
                    ("model", estimator),
                ]
            )
            model_pipeline.fit(X_train, y_train)
        else:
            raise

    preds = model_pipeline.predict(X_test)
    rmse = float(np.sqrt(mean_squared_error(y_test, preds)))
    mae = float(mean_absolute_error(y_test, preds))

    model_dir = data_dir / "processed" / "models"
    model_dir.mkdir(parents=True, exist_ok=True)

    model_path = model_dir / f"lap_time_baseline_xgb_{season}.joblib"
    metrics_path = model_dir / f"lap_time_baseline_xgb_{season}_metrics.json"
    joblib.dump(model_pipeline, model_path)

    metrics_payload = {
        "season": season,
        "model_type": "xgboost_regressor",
        "rmse": rmse,
        "mae": mae,
        "used_gpu": used_gpu,
        "rows": int(len(df)),
    }
    metrics_path.write_text(json.dumps(metrics_payload, indent=2), encoding="utf-8")

    return {
        "model_path": str(model_path),
        "metrics_path": str(metrics_path),
        "rmse": rmse,
        "mae": mae,
        "used_gpu": used_gpu,
    }
