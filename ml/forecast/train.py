"""
Revenue Forecasting — Facebook Prophet
Dataset: UCI Bank Marketing + transaction history
"""
import pandas as pd
import numpy as np

# Prophet uses np.float_ which was removed in NumPy 2.0
if not hasattr(np, "float_"):
    np.float_ = np.float64

from prophet import Prophet
from prophet.diagnostics import cross_validation, performance_metrics
import joblib
import json
from pathlib import Path
from typing import Optional

MODEL_DIR = Path(__file__).parent / "artifacts"
MODEL_DIR.mkdir(exist_ok=True)


def prepare_prophet_df(df: pd.DataFrame, date_col: str = "date", value_col: str = "revenue") -> pd.DataFrame:
    prophet_df = pd.DataFrame()
    prophet_df["ds"] = pd.to_datetime(df[date_col])
    prophet_df["y"] = pd.to_numeric(df[value_col], errors="coerce")
    prophet_df = prophet_df.dropna().sort_values("ds")
    return prophet_df


def train(df: pd.DataFrame, date_col: str = "date", value_col: str = "revenue",
          branch_id: Optional[int] = None):
    prophet_df = prepare_prophet_df(df, date_col, value_col)

    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=False,
        seasonality_mode="multiplicative",
        changepoint_prior_scale=0.05,
        seasonality_prior_scale=10.0,
        uncertainty_samples=1000,
    )

    model.add_country_holidays(country_name="PK")

    model.fit(prophet_df)

    # Cross validation (only if enough data)
    metrics = {}
    if len(prophet_df) >= 60:
        try:
            cv_df = cross_validation(model, initial="30 days", period="7 days", horizon="14 days")
            pm = performance_metrics(cv_df)
            metrics = {
                "mae": float(pm["mae"].mean()),
                "rmse": float(pm["rmse"].mean()),
                "mape": float(pm["mape"].mean()),
            }
            print(f"Forecast Model — MAE: {metrics['mae']:.2f} | MAPE: {metrics['mape']:.4f}")
        except Exception:
            pass

    suffix = f"_{branch_id}" if branch_id else ""
    joblib.dump(model, MODEL_DIR / f"forecast_model{suffix}.pkl")
    with open(MODEL_DIR / f"forecast_metrics{suffix}.json", "w") as f:
        json.dump(metrics, f)

    return model, metrics


def load_model(branch_id: Optional[int] = None):
    suffix = f"_{branch_id}" if branch_id else ""
    path = MODEL_DIR / f"forecast_model{suffix}.pkl"
    if not path.exists():
        path = MODEL_DIR / "forecast_model.pkl"
    try:
        model = joblib.load(path)
        # Validate model is compatible with current Prophet version
        model.history  # validates model loaded correctly
        return model
    except Exception:
        # Model file is stale / version-incompatible — remove so UI prompts retrain
        try:
            path.unlink(missing_ok=True)
        except Exception:
            pass
        raise FileNotFoundError(f"Forecast model is outdated. Please retrain from the Train tab.")


if __name__ == "__main__":
    np.random.seed(42)
    dates = pd.date_range("2020-01-01", "2024-12-31", freq="D")
    n = len(dates)
    trend = np.linspace(100000, 500000, n)
    seasonality = 50000 * np.sin(2 * np.pi * np.arange(n) / 365)
    noise = np.random.normal(0, 15000, n)
    revenue = trend + seasonality + noise
    df = pd.DataFrame({"date": dates, "revenue": revenue})
    train(df)
