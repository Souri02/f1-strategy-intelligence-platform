from __future__ import annotations

from itertools import product
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd


def _validate_paths(data_dir: Path, season: int) -> tuple[Path, Path]:
    features_path = data_dir / "processed" / f"lap_features_{season}.parquet"
    model_path = data_dir / "processed" / "models" / f"lap_time_baseline_xgb_{season}.joblib"
    if not features_path.exists():
        raise FileNotFoundError(
            f"{features_path} not found. Build lap features before running simulation."
        )
    if not model_path.exists():
        raise FileNotFoundError(
            f"{model_path} not found. Train lap-time model before running simulation."
        )
    return features_path, model_path


def _feature_columns() -> list[str]:
    return [
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


def _simulate_race_time(model: Any, scenario_df: pd.DataFrame) -> float:
    preds = model.predict(scenario_df[_feature_columns()])
    first_lap = float(scenario_df["lap_time_seconds"].iloc[0])
    return float(first_lap + preds.sum())


def _estimate_pit_stop_loss_seconds(race_df: pd.DataFrame) -> float:
    typical_lap = float(race_df["lap_time_seconds"].median())
    pit_in_penalty = max(2.5, typical_lap * 0.035)
    pit_out_penalty = max(6.0, typical_lap * 0.08)
    return pit_in_penalty + pit_out_penalty


def _apply_race_constraints(
    requested_lap: int,
    max_lap: int,
    min_stint_laps: int = 8,
) -> tuple[int, int, int, list[str]]:
    constraints_applied: list[str] = []
    feasible_start = max(2, min_stint_laps)
    feasible_end = max(feasible_start + 1, max_lap - min_stint_laps)

    constrained_lap = requested_lap
    if constrained_lap < feasible_start:
        constrained_lap = feasible_start
        constraints_applied.append("pit lap moved to satisfy minimum first-stint length")
    if constrained_lap > feasible_end:
        constrained_lap = feasible_end
        constraints_applied.append("pit lap moved to satisfy minimum second-stint length")

    if constrained_lap > max_lap - 1:
        constrained_lap = max_lap - 1
        constraints_applied.append("pit lap capped at race end minus one lap")
    if constrained_lap < 2:
        constrained_lap = 2
        constraints_applied.append("pit lap raised to earliest valid race lap")

    return constrained_lap, feasible_start, feasible_end, constraints_applied


def _apply_counterfactual(
    df: pd.DataFrame,
    pit_lap: int,
    counterfactual_compound: str,
) -> pd.DataFrame:
    scenario_df = df.copy()
    scenario_df["is_pit_in_lap"] = False
    scenario_df["is_pit_out_lap"] = False

    scenario_df.loc[scenario_df["lap_number"] == pit_lap, "is_pit_in_lap"] = True
    scenario_df.loc[scenario_df["lap_number"] == pit_lap + 1, "is_pit_out_lap"] = True
    scenario_df["compound"] = scenario_df["compound"].astype(str)
    scenario_df.loc[scenario_df["lap_number"] >= pit_lap + 1, "compound"] = counterfactual_compound

    baseline_first_stint = int(scenario_df["stint"].min())
    scenario_df.loc[scenario_df["lap_number"] <= pit_lap, "stint"] = baseline_first_stint
    scenario_df.loc[scenario_df["lap_number"] >= pit_lap + 1, "stint"] = baseline_first_stint + 1
    scenario_df["tire_life"] = (
        scenario_df["lap_number"] - pit_lap
    ).clip(lower=1).where(scenario_df["lap_number"] >= pit_lap + 1, scenario_df["tire_life"])
    return scenario_df


def _apply_strategy_plan(
    df: pd.DataFrame,
    pit_laps: list[int],
    compounds: list[str],
) -> pd.DataFrame:
    scenario_df = df.copy()
    scenario_df["is_pit_in_lap"] = False
    scenario_df["is_pit_out_lap"] = False
    scenario_df["compound"] = scenario_df["compound"].astype(str)
    base_stint = int(scenario_df["stint"].min())

    all_pit_laps = sorted(pit_laps)
    for idx, pit_lap in enumerate(all_pit_laps):
        scenario_df.loc[scenario_df["lap_number"] == pit_lap, "is_pit_in_lap"] = True
        scenario_df.loc[scenario_df["lap_number"] == pit_lap + 1, "is_pit_out_lap"] = True
        compound_idx = min(idx, len(compounds) - 1)
        scenario_df.loc[scenario_df["lap_number"] >= pit_lap + 1, "compound"] = compounds[compound_idx]

    bounds = [1] + [lap + 1 for lap in all_pit_laps] + [int(scenario_df["lap_number"].max()) + 1]
    for stint_idx in range(len(bounds) - 1):
        start = bounds[stint_idx]
        end = bounds[stint_idx + 1]
        mask = (scenario_df["lap_number"] >= start) & (scenario_df["lap_number"] < end)
        scenario_df.loc[mask, "stint"] = base_stint + stint_idx
        scenario_df.loc[mask, "tire_life"] = scenario_df.loc[mask, "lap_number"] - start + 1
    return scenario_df


def _simulate_with_uncertainty(
    model: Any,
    scenario_df: pd.DataFrame,
    lap_std: float,
    samples: int,
) -> tuple[float, float]:
    base_time = _simulate_race_time(model, scenario_df)
    sample_noise = np.random.normal(loc=0.0, scale=max(0.8, lap_std * 0.18), size=samples)
    sampled_totals = base_time + sample_noise
    return float(sampled_totals.mean()), float(sampled_totals.std(ddof=1))


def _generate_candidate_plans(
    feasible_start: int,
    feasible_end: int,
) -> list[tuple[str, list[int], list[str]]]:
    plans: list[tuple[str, list[int], list[str]]] = []
    one_stop_laps = list(range(feasible_start, feasible_end + 1, 2))
    for lap in one_stop_laps:
        for comp in ["SOFT", "MEDIUM", "HARD"]:
            plans.append(("one_stop", [lap], [comp]))

    for first in range(feasible_start, feasible_end - 10, 5):
        for second in range(first + 8, feasible_end + 1, 5):
            for c1, c2 in product(["SOFT", "MEDIUM", "HARD"], repeat=2):
                if c1 == c2:
                    continue
                plans.append(("two_stop", [first, second], [c1, c2]))
    return plans


def _compute_explainability(
    model: Any,
    scenario_df: pd.DataFrame,
) -> dict[str, float]:
    base_time = _simulate_race_time(model, scenario_df)
    impacts: dict[str, float] = {}

    modified = scenario_df.copy()
    modified["tire_life"] = modified["tire_life"] + 3
    impacts["tire_life"] = float(_simulate_race_time(model, modified) - base_time)

    modified = scenario_df.copy()
    modified["position"] = modified["position"].clip(lower=1) + 1
    impacts["track_position"] = float(_simulate_race_time(model, modified) - base_time)

    modified = scenario_df.copy()
    modified["is_safety_car_like"] = True
    impacts["safety_car_state"] = float(_simulate_race_time(model, modified) - base_time)

    modified = scenario_df.copy()
    modified["lap_time_seconds"] = modified["lap_time_seconds"] + 0.6
    impacts["current_pace_signal"] = float(_simulate_race_time(model, modified) - base_time)
    return impacts


def run_strategy_counterfactual(
    data_dir: Path,
    season: int,
    round_no: int,
    driver: str,
    baseline_pit_lap: int,
    counterfactual_pit_lap: int,
    counterfactual_compound: str,
) -> dict[str, Any]:
    features_path, model_path = _validate_paths(data_dir, season)
    feature_df = pd.read_parquet(features_path)
    model = joblib.load(model_path)

    driver = driver.upper()
    race_df = feature_df[
        (feature_df["season"] == season)
        & (feature_df["round"] == round_no)
        & (feature_df["driver"] == driver)
    ].copy()
    race_df = race_df.sort_values("lap_number").dropna(subset=["lap_number", "lap_time_seconds"])

    if race_df.empty or len(race_df) < 10:
        raise ValueError(
            f"Insufficient lap feature data for season={season}, round={round_no}, driver={driver}."
        )

    max_lap = int(race_df["lap_number"].max())
    baseline_lap, feasible_start, feasible_end, baseline_constraints = _apply_race_constraints(
        baseline_pit_lap, max_lap=max_lap
    )
    counter_lap, _, _, counter_constraints = _apply_race_constraints(
        counterfactual_pit_lap, max_lap=max_lap
    )
    all_constraints = baseline_constraints + counter_constraints

    baseline_df = _apply_counterfactual(
        race_df,
        pit_lap=baseline_lap,
        counterfactual_compound=race_df["compound"].mode().iloc[0] if not race_df["compound"].mode().empty else "MEDIUM",
    )
    counter_df = _apply_counterfactual(
        race_df,
        pit_lap=counter_lap,
        counterfactual_compound=counterfactual_compound.upper(),
    )

    pit_loss_seconds = _estimate_pit_stop_loss_seconds(race_df)
    baseline_time = _simulate_race_time(model, baseline_df) + pit_loss_seconds
    counter_time = _simulate_race_time(model, counter_df) + pit_loss_seconds
    delta_seconds = counter_time - baseline_time
    lap_std = float(race_df["lap_time_seconds"].std(ddof=1)) if len(race_df) > 1 else 2.5
    uncertainty = max(1.5, 0.4 * lap_std + 0.15 * abs(counter_lap - baseline_lap))
    delta_low = float(delta_seconds - 1.96 * uncertainty)
    delta_high = float(delta_seconds + 1.96 * uncertainty)
    estimated_position_gain = int(round(-delta_seconds / 2.2))
    recommended_pit_lap = counter_lap if counter_time < baseline_time else baseline_lap

    return {
        "season": season,
        "round": round_no,
        "driver": driver,
        "baseline_pit_lap": baseline_lap,
        "counterfactual_pit_lap": counter_lap,
        "baseline_estimated_time_seconds": float(baseline_time),
        "counterfactual_estimated_time_seconds": float(counter_time),
        "delta_seconds": float(delta_seconds),
        "delta_confidence_low_seconds": delta_low,
        "delta_confidence_high_seconds": delta_high,
        "pit_stop_loss_seconds": float(pit_loss_seconds),
        "estimated_position_gain": estimated_position_gain,
        "recommended_pit_lap": recommended_pit_lap,
        "feasible_pit_window_start": feasible_start,
        "feasible_pit_window_end": feasible_end,
        "constraints_applied": all_constraints,
    }


def optimize_strategy_plan(
    data_dir: Path,
    season: int,
    round_no: int,
    driver: str,
    baseline_pit_lap: int,
    monte_carlo_samples: int = 200,
) -> dict[str, Any]:
    features_path, model_path = _validate_paths(data_dir, season)
    feature_df = pd.read_parquet(features_path)
    model = joblib.load(model_path)
    driver = driver.upper()

    race_df = feature_df[
        (feature_df["season"] == season)
        & (feature_df["round"] == round_no)
        & (feature_df["driver"] == driver)
    ].copy()
    race_df = race_df.sort_values("lap_number").dropna(subset=["lap_number", "lap_time_seconds"])
    if race_df.empty or len(race_df) < 10:
        raise ValueError(
            f"Insufficient lap feature data for season={season}, round={round_no}, driver={driver}."
        )

    max_lap = int(race_df["lap_number"].max())
    baseline_lap, feasible_start, feasible_end, _ = _apply_race_constraints(
        baseline_pit_lap, max_lap=max_lap
    )
    baseline_df = _apply_strategy_plan(race_df, [baseline_lap], ["MEDIUM"])
    lap_std = float(race_df["lap_time_seconds"].std(ddof=1)) if len(race_df) > 1 else 2.5
    pit_loss_seconds = _estimate_pit_stop_loss_seconds(race_df)
    baseline_mean, _ = _simulate_with_uncertainty(
        model, baseline_df, lap_std=lap_std, samples=monte_carlo_samples
    )
    baseline_time = baseline_mean + pit_loss_seconds

    candidates: list[dict[str, Any]] = []
    for label, pit_laps, compounds in _generate_candidate_plans(feasible_start, feasible_end):
        scenario_df = _apply_strategy_plan(race_df, pit_laps, compounds)
        mean_time, std_time = _simulate_with_uncertainty(
            model, scenario_df, lap_std=lap_std, samples=monte_carlo_samples
        )
        total_time = mean_time + pit_loss_seconds * len(pit_laps)
        gain = int(round((baseline_time - total_time) / 2.2))
        candidates.append(
            {
                "strategy_label": label,
                "pit_laps": pit_laps,
                "compounds": compounds,
                "estimated_time_seconds": float(total_time),
                "uncertainty_seconds": float(std_time),
                "position_gain_vs_baseline": gain,
            }
        )

    candidates = sorted(candidates, key=lambda x: x["estimated_time_seconds"])
    best = candidates[0]
    explainability = _compute_explainability(
        model,
        _apply_strategy_plan(race_df, best["pit_laps"], best["compounds"]),
    )
    return {
        "season": season,
        "round": round_no,
        "driver": driver,
        "baseline_estimated_time_seconds": float(baseline_time),
        "best_strategy": best,
        "top_candidates": candidates[:5],
        "explainability": explainability,
    }
