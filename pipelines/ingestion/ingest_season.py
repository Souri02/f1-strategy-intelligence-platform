import argparse
from pathlib import Path

from app.services.ingestion import ingest_season_data


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest F1 season-level data.")
    parser.add_argument("--season", type=int, required=True, help="Season year (e.g., 2024)")
    parser.add_argument("--data-dir", type=Path, default=Path("./data"), help="Data output directory")
    parser.add_argument(
        "--include-telemetry",
        action="store_true",
        help="Reserved for Phase 2 telemetry ingestion",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    stats = ingest_season_data(
        data_dir=args.data_dir,
        season=args.season,
        include_telemetry=args.include_telemetry,
    )
    print(
        f"Done. season={args.season} schedule_rows={stats['schedule_rows']} "
        f"results_rows={stats['results_rows']}"
    )


if __name__ == "__main__":
    main()
