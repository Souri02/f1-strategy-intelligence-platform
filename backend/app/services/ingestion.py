from __future__ import annotations

from pathlib import Path
from typing import Any

import fastf1
import pandas as pd
import requests

from app.services.storage import ensure_data_dirs, write_parquet

ERGAST_FALLBACK = "https://ergast.com/api/f1/{season}/results.json?limit=1000"
JOLPICA_PRIMARY = "https://api.jolpi.ca/ergast/f1/{season}/results.json?limit=1000"


def _extract_results_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    races = payload["MRData"]["RaceTable"]["Races"]
    rows: list[dict[str, Any]] = []
    for race in races:
        race_name = race.get("raceName")
        round_no = race.get("round")
        race_date = race.get("date")
        circuit_name = race.get("Circuit", {}).get("circuitName")
        for result in race.get("Results", []):
            driver = result.get("Driver", {}) or {}
            constructor = result.get("Constructor", {}) or {}
            rows.append(
                {
                    "season": race.get("season"),
                    "round": round_no,
                    "race_name": race_name,
                    "race_date": race_date,
                    "circuit_name": circuit_name,
                    "driver_code": driver.get("code"),
                    "driver_id": driver.get("driverId"),
                    "driver_given_name": driver.get("givenName"),
                    "driver_family_name": driver.get("familyName"),
                    "driver_url": driver.get("url"),
                    "constructor_id": constructor.get("constructorId"),
                    "constructor_name": constructor.get("name"),
                    "constructor_url": constructor.get("url"),
                    "grid": result.get("grid"),
                    "position": result.get("position"),
                    "points": result.get("points"),
                    "status": result.get("status"),
                    "laps": result.get("laps"),
                    "time_ms": result.get("Time", {}).get("millis"),
                }
            )
    return rows


def _download_season_results(season: int) -> pd.DataFrame:
    urls = [
        JOLPICA_PRIMARY.format(season=season),
        ERGAST_FALLBACK.format(season=season),
    ]
    for url in urls:
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            rows = _extract_results_rows(response.json())
            if rows:
                return pd.DataFrame(rows)
        except (requests.RequestException, KeyError):
            continue
    # Fallback (no external quota): build results from FastF1 session results.
    try:
        schedule_df = fastf1.get_event_schedule(season, include_testing=False)
        race_events = schedule_df[schedule_df["EventFormat"] != "testing"]
        rows: list[dict[str, Any]] = []
        for _, event in race_events.iterrows():
            round_no = int(event["RoundNumber"])
            event_name = event["EventName"]
            try:
                session = fastf1.get_session(season, round_no, "R")
                session.load(laps=False, telemetry=False, weather=False, messages=False)
                results = session.results
            except Exception:
                continue
            if results is None or len(results) == 0:
                continue
            for _, r in results.iterrows():
                driver_code = r.get("Abbreviation") or r.get("Abbreviation".lower())
                full_name = r.get("FullName") or r.get("FullName".lower()) or ""
                given_name = None
                family_name = None
                if isinstance(full_name, str) and full_name.strip():
                    parts = full_name.strip().split(" ")
                    if len(parts) >= 2:
                        given_name = " ".join(parts[:-1])
                        family_name = parts[-1]
                rows.append(
                    {
                        "season": season,
                        "round": round_no,
                        "race_name": event_name,
                        "race_date": None,
                        "circuit_name": None,
                        "driver_code": driver_code,
                        "driver_id": None,
                        "driver_given_name": given_name,
                        "driver_family_name": family_name,
                        "driver_url": None,
                        "constructor_id": r.get("TeamName"),
                        "constructor_name": r.get("TeamName"),
                        "constructor_url": None,
                        "grid": r.get("GridPosition"),
                        "position": r.get("Position"),
                        "points": r.get("Points"),
                        "status": r.get("Status"),
                        "laps": None,
                        "time_ms": None,
                    }
                )
        if rows:
            return pd.DataFrame(rows)
    except Exception:
        pass

    raise RuntimeError(
        f"Failed to fetch season results for {season} from public APIs and FastF1 fallback."
    )


def _safe_float(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def ingest_lap_data(season: int) -> pd.DataFrame:
    schedule_df = fastf1.get_event_schedule(season, include_testing=False)
    race_events = schedule_df[schedule_df["EventFormat"] != "testing"]
    lap_rows: list[dict[str, Any]] = []

    for _, event in race_events.iterrows():
        round_no = int(event["RoundNumber"])
        event_name = event["EventName"]
        try:
            session = fastf1.get_session(season, round_no, "R")
            session.load(laps=True, telemetry=False, weather=False, messages=False)
            laps_df = session.laps.copy()
        except Exception:
            # Skip events that are unavailable or fail to load.
            continue

        if laps_df.empty:
            continue

        for _, lap in laps_df.iterrows():
            lap_time_sec = lap.get("LapTime")
            lap_time_sec = lap_time_sec.total_seconds() if pd.notna(lap_time_sec) else None
            pit_out = lap.get("PitOutTime")
            pit_in = lap.get("PitInTime")
            lap_rows.append(
                {
                    "season": season,
                    "round": round_no,
                    "event_name": event_name,
                    "driver": lap.get("Driver"),
                    "team": lap.get("Team"),
                    "lap_number": int(lap.get("LapNumber")) if pd.notna(lap.get("LapNumber")) else None,
                    "lap_time_seconds": lap_time_sec,
                    "stint": int(lap.get("Stint")) if pd.notna(lap.get("Stint")) else None,
                    "compound": lap.get("Compound"),
                    "tire_life": _safe_float(lap.get("TyreLife")),
                    "track_status": str(lap.get("TrackStatus")) if pd.notna(lap.get("TrackStatus")) else None,
                    "position": int(lap.get("Position")) if pd.notna(lap.get("Position")) else None,
                    "is_pit_out_lap": pd.notna(pit_out),
                    "is_pit_in_lap": pd.notna(pit_in),
                }
            )

    return pd.DataFrame(lap_rows)


def ingest_season_data(data_dir: Path, season: int, include_telemetry: bool = False) -> dict[str, int]:
    ensure_data_dirs(data_dir)

    cache_dir = data_dir / "raw" / "fastf1_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    fastf1.Cache.enable_cache(str(cache_dir))
    schedule_df = fastf1.get_event_schedule(season, include_testing=False)
    results_df = _download_season_results(season)

    write_parquet(schedule_df, data_dir / "raw" / f"schedule_{season}.parquet")
    write_parquet(results_df, data_dir / "raw" / f"results_{season}.parquet")

    if include_telemetry:
        laps_df = ingest_lap_data(season)
        write_parquet(laps_df, data_dir / "raw" / f"laps_{season}.parquet")

    return {
        "schedule_rows": len(schedule_df),
        "results_rows": len(results_df),
    }
