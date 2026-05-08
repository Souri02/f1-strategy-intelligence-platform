from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd


def _wiki_title_from_url(url: str | None) -> str | None:
    if not url:
        return None
    try:
        parsed = urlparse(url)
        if "wikipedia.org" not in (parsed.netloc or ""):
            return None
        parts = (parsed.path or "").split("/")
        if "wiki" not in parts:
            return None
        idx = parts.index("wiki")
        title = parts[idx + 1] if idx + 1 < len(parts) else None
        return title
    except Exception:
        return None


@dataclass(frozen=True)
class DriverMeta:
    code: str
    full_name: str | None
    constructor: str | None
    wikipedia_title: str | None


@dataclass(frozen=True)
class TeamMeta:
    constructor_id: str | None
    constructor_name: str | None
    wikipedia_title: str | None


def load_driver_team_metadata(data_dir: Path, season: int) -> tuple[list[DriverMeta], list[TeamMeta]]:
    results_path = data_dir / "raw" / f"results_{season}.parquet"
    if not results_path.exists():
        raise FileNotFoundError(
            f"{results_path} not found. Prepare season {season} first (ingestion)."
        )

    df = pd.read_parquet(results_path)
    for col in ["driver_code", "constructor_name", "constructor_id"]:
        if col not in df.columns:
            raise ValueError(
                f"results_{season}.parquet missing required column '{col}'. Re-run ingestion for {season}."
            )

    df = df.copy()
    df["driver_code"] = df["driver_code"].astype(str).str.upper()

    if "driver_given_name" in df.columns and "driver_family_name" in df.columns:
        df["driver_full_name"] = (
            df["driver_given_name"].fillna("").astype(str).str.strip()
            + " "
            + df["driver_family_name"].fillna("").astype(str).str.strip()
        ).str.strip()
    else:
        df["driver_full_name"] = None

    if "driver_url" in df.columns:
        df["driver_wiki"] = df["driver_url"].apply(_wiki_title_from_url)
    else:
        df["driver_wiki"] = None

    if "constructor_url" in df.columns:
        df["constructor_wiki"] = df["constructor_url"].apply(_wiki_title_from_url)
    else:
        df["constructor_wiki"] = None

    drivers: dict[str, DriverMeta] = {}
    for _, r in df.dropna(subset=["driver_code"]).iterrows():
        code = str(r["driver_code"]).upper()
        if code in drivers:
            continue
        drivers[code] = DriverMeta(
            code=code,
            full_name=r.get("driver_full_name") or None,
            constructor=r.get("constructor_name") or None,
            wikipedia_title=r.get("driver_wiki") or None,
        )

    teams: dict[str, TeamMeta] = {}
    for _, r in df.dropna(subset=["constructor_name"]).iterrows():
        name = str(r.get("constructor_name"))
        if name in teams:
            continue
        teams[name] = TeamMeta(
            constructor_id=r.get("constructor_id") or None,
            constructor_name=r.get("constructor_name") or None,
            wikipedia_title=r.get("constructor_wiki") or None,
        )

    return sorted(drivers.values(), key=lambda x: x.code), sorted(
        teams.values(), key=lambda x: (x.constructor_name or "")
    )

