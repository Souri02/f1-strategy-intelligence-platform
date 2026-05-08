from app.main_lite import app

# Vercel: use lite app (no sklearn/xgboost) to stay under Lambda bundle limits.
# Full API: Docker / uvicorn app.full_app:app

