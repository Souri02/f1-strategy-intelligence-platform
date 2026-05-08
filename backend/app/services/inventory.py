from __future__ import annotations

from pathlib import Path


def available_seasons(data_dir: Path) -> dict[str, list[int]]:
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    models_dir = processed_dir / "models"

    def _years_from(pattern: str, root: Path) -> set[int]:
        years: set[int] = set()
        for p in root.glob(pattern):
            stem = p.stem
            # e.g. lap_features_2024 -> last token
            try:
                year = int(stem.split("_")[-1])
                years.add(year)
            except Exception:
                continue
        return years

    return {
        "raw_laps": sorted(_years_from("laps_*.parquet", raw_dir)) if raw_dir.exists() else [],
        "features": sorted(_years_from("lap_features_*.parquet", processed_dir)) if processed_dir.exists() else [],
        "models": sorted(_years_from("lap_time_baseline_xgb_*.joblib", models_dir)) if models_dir.exists() else [],
    }

