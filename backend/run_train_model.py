import argparse

from app.config import settings
from app.services.model_training import train_lap_time_baseline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train baseline lap-time model.")
    parser.add_argument("--season", type=int, default=settings.default_season)
    parser.add_argument("--use-gpu", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    stats = train_lap_time_baseline(
        data_dir=settings.data_dir,
        season=args.season,
        use_gpu=args.use_gpu,
    )
    print(
        "Training complete. "
        f"rmse={stats['rmse']:.4f} mae={stats['mae']:.4f} "
        f"used_gpu={stats['used_gpu']} model={stats['model_path']}"
    )


if __name__ == "__main__":
    main()
