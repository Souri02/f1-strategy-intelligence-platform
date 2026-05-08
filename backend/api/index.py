from app.main_lite import app

# Vercel: use lite app (no sklearn/xgboost) to stay under Lambda bundle limits.
# Full API: Docker image or local uvicorn with app.main:app

