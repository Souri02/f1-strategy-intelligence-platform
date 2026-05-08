from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.services.storage import ensure_data_dirs, write_parquet


def build_lap_feature_table(data_dir: Path, season: int) -> tuple[pd.DataFrame, Path]:
    ensure_data_dirs(data_dir)
    laps_path = data_dir / "raw" / f"laps_{season}.parquet"
    results_path = data_dir / "raw" / f"results_{season}.parquet"

    if not laps_path.exists():
        raise FileNotFoundError(
            f"{laps_path} not found. Run ingestion with include_telemetry=true first."
        )
    if not results_path.exists():
        raise FileNotFoundError(f"{results_path} not found. Run season ingestion first.")

    laps_df = pd.read_parquet(laps_path)
    results_df = pd.read_parquet(results_path)
    laps_df["season"] = pd.to_numeric(laps_df["season"], errors="coerce").astype("Int64")
    laps_df["round"] = pd.to_numeric(laps_df["round"], errors="coerce").astype("Int64")
    results_df["season"] = pd.to_numeric(results_df["season"], errors="coerce").astype("Int64")
    results_df["round"] = pd.to_numeric(results_df["round"], errors="coerce").astype("Int64")

    results_df = results_df[["season", "round", "driver_code", "position", "grid", "points"]].copy()
    results_df = results_df.rename(
        columns={
            "driver_code": "driver",
            "position": "final_position",
            "grid": "grid_position",
            "points": "race_points",
        }
    )

    merged = laps_df.merge(results_df, on=["season", "round", "driver"], how="left")
    merged = merged.sort_values(["season", "round", "driver", "lap_number"])

    merged["next_lap_time_seconds"] = merged.groupby(["season", "round", "driver"])[
        "lap_time_seconds"
    ].shift(-1)
    merged["lap_time_delta"] = merged["next_lap_time_seconds"] - merged["lap_time_seconds"]
    merged["is_safety_car_like"] = merged["track_status"].astype(str).str.contains("4|6|7", regex=True)

    feature_df = merged[
        [
            "season",
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
            "next_lap_time_seconds",
            "lap_time_delta",
        ]
    ].copy()

    feature_df = feature_df.dropna(subset=["lap_time_seconds", "next_lap_time_seconds"])
    output_path = data_dir / "processed" / f"lap_features_{season}.parquet"
    write_parquet(feature_df, output_path)
    return feature_df, output_path
