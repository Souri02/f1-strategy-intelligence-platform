import argparse

from app.config import settings
from app.services.feature_engineering import build_lap_feature_table


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build lap features from raw telemetry/laps.")
    parser.add_argument("--season", type=int, default=settings.default_season)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    feature_df, output_path = build_lap_feature_table(settings.data_dir, args.season)
    print(f"Feature build complete. rows={len(feature_df)} output={output_path}")


if __name__ == "__main__":
    main()
