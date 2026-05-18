import pandas as pd
import numpy as np
from typing import Optional

if not hasattr(np, "float_"):
    np.float_ = np.float64

from ml.forecast.train import load_model

_models = {}


def _get_model(branch_id: Optional[int] = None):
    key = branch_id or "global"
    if key not in _models:
        _models[key] = load_model(branch_id)
    return _models[key]


def forecast(periods: int = 30, freq: str = "D",
             branch_id: Optional[int] = None) -> pd.DataFrame:
    from datetime import datetime
    model = _get_model(branch_id)

    # If the model was trained on old data, extend enough to reach today + periods
    last_train_date = model.history["ds"].max()
    days_since_training = max(0, (datetime.now() - last_train_date).days)
    total_periods = days_since_training + periods

    future = model.make_future_dataframe(periods=total_periods, freq=freq)
    forecast_df = model.predict(future)

    result = forecast_df[["ds", "yhat", "yhat_lower", "yhat_upper",
                           "trend", "weekly", "yearly"]].copy()
    result.columns = ["date", "forecast", "lower_bound", "upper_bound",
                      "trend", "weekly_seasonality", "yearly_seasonality"]
    result["date"] = result["date"].dt.strftime("%Y-%m-%d")
    result["forecast"] = result["forecast"].round(2)
    result["lower_bound"] = result["lower_bound"].round(2)
    result["upper_bound"] = result["upper_bound"].round(2)
    return result


def forecast_summary(periods: int = 30, branch_id: Optional[int] = None) -> dict:
    df = forecast(periods=periods, branch_id=branch_id)
    future = df.tail(periods)
    return {
        "forecast_period_days": periods,
        "total_forecast_revenue": round(future["forecast"].sum(), 2),
        "avg_daily_revenue": round(future["forecast"].mean(), 2),
        "peak_day": future.loc[future["forecast"].idxmax(), "date"],
        "peak_revenue": round(future["forecast"].max(), 2),
        "min_day": future.loc[future["forecast"].idxmin(), "date"],
        "min_revenue": round(future["forecast"].min(), 2),
        "growth_rate_pct": round(
            (future["forecast"].iloc[-1] - future["forecast"].iloc[0])
            / (abs(future["forecast"].iloc[0]) + 1e-8) * 100, 2
        ),
        "data": future.to_dict(orient="records"),
    }
