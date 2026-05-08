#!/usr/bin/env python3
"""
Verify all runtime imports used by the backend resolve after `pip install -r requirements.txt`.
Run from repo root: python scripts/verify_environment.py
Or from backend with PYTHONPATH: cd backend && python ../scripts/verify_environment.py
"""
from __future__ import annotations

import importlib
import subprocess
import sys
from pathlib import Path

# Third-party packages that must be importable (map to pip package names where different)
REQUIRED_MODULES = [
    ("fastapi", "fastapi"),
    ("uvicorn", "uvicorn"),
    ("pydantic", "pydantic"),
    ("pydantic_settings", "pydantic-settings"),
    ("pandas", "pandas"),
    ("numpy", "numpy"),
    ("requests", "requests"),
    ("fastf1", "fastf1"),
    ("pyarrow", "pyarrow"),
    ("dotenv", "python-dotenv"),
    ("sklearn", "scikit-learn"),
    ("xgboost", "xgboost"),
    ("joblib", "joblib"),
]


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    # Repo checkout: backend/app/...  |  Docker image: /app/app/...
    backend_dir = root / "backend"
    if (backend_dir / "app").is_dir():
        sys.path.insert(0, str(backend_dir))
    elif (root / "app").is_dir():
        sys.path.insert(0, str(root))
    else:
        print("Cannot find backend app package; run from repo root or use Docker image layout.", file=sys.stderr)
        return 1

    failed: list[tuple[str, str, str]] = []
    for module_name, pip_name in REQUIRED_MODULES:
        try:
            importlib.import_module(module_name)
        except ImportError as exc:
            failed.append((module_name, pip_name, str(exc)))

    if failed:
        print("Missing or broken imports (install with: pip install -r backend/requirements.txt)")
        for mod, pip, err in failed:
            print(f"  - {mod} (pip: {pip}): {err}")
        return 1

    # App package smoke test
    try:
        import app.main  # noqa: F401
        import app.api.routes  # noqa: F401
        import app.services.strategy_simulation  # noqa: F401
    except Exception as exc:
        print(f"App import failed: {exc}")
        return 1

    pip_check = subprocess.run(
        [sys.executable, "-m", "pip", "check"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if pip_check.returncode != 0:
        print("pip check reported issues (broken or conflicting requirements):")
        print(pip_check.stdout or pip_check.stderr or "(no output)")
        return 1

    print("OK: All required packages and app modules import successfully.")
    print("OK: pip check passed (no broken dependencies).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
