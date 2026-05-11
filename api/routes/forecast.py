from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, List
from api.middleware.rate_limit import limiter
from api.routes.auth import get_current_user

router = APIRouter(prefix="/forecast", tags=["Revenue Forecasting"])


@router.get("/predict")
@limiter.limit("20/minute")
async def get_forecast(request: Request, periods: int = 30,
                        branch_id: Optional[int] = None,
                        current_user=Depends(get_current_user)):
    from ml.forecast.predict import forecast_summary
    try:
        return forecast_summary(periods=periods, branch_id=branch_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Forecast model not trained yet. Upload data first.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trend")
async def get_historical_trend(branch_id: Optional[int] = None,
                                 current_user=Depends(get_current_user)):
    from ml.forecast.predict import forecast
    try:
        df = forecast(periods=0, branch_id=branch_id)
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
