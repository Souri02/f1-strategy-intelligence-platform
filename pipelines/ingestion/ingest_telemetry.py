import argparse

from app.config import settings
from app.services.ingestion import ingest_season_data


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest F1 lap telemetry-style data.")
    parser.add_argument("--season", type=int, default=settings.default_season)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    stats = ingest_season_data(
        data_dir=settings.data_dir,
        season=args.season,
        include_telemetry=True,
    )
    print(
        f"Telemetry ingestion complete for season {args.season}. "
        f"schedule_rows={stats['schedule_rows']}, results_rows={stats['results_rows']}"
    )


if __name__ == "__main__":
    main()
