from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from db.connection import get_db
from api.middleware.rate_limit import limiter
from api.routes.auth import get_current_user

router = APIRouter(prefix="/churn", tags=["Churn Prediction"])


class CustomerInput(BaseModel):
    credit_score: int
    age: int
    tenure: int
    balance: float
    num_products: int
    has_credit_card: int = 1
    is_active_member: int = 1
    estimated_salary: float
    geography: Optional[str] = "Karachi"
    gender: Optional[str] = "Male"


@router.post("/predict")
@limiter.limit("30/minute")
async def predict_churn(request: Request, customer: CustomerInput,
                         db: Session = Depends(get_db),
                         current_user=Depends(get_current_user)):
    from ml.churn.predict import predict_single
    try:
        result = predict_single(customer.dict())
        from services.alert_service import send_churn_alert
        from config.settings import settings
        if result["churn_probability"] >= settings.CHURN_ALERT_THRESHOLD:
            send_churn_alert(
                customer_id=0,
                customer_name="API Request",
                churn_probability=result["churn_probability"],
            )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predict/batch")
@limiter.limit("5/minute")
async def predict_churn_batch(request: Request, customers: List[dict],
                               current_user=Depends(get_current_user)):
    import pandas as pd
    from ml.churn.predict import predict_batch
    try:
        df = pd.DataFrame(customers)
        result_df = predict_batch(df)
        return {"count": len(result_df), "results": result_df.to_dict(orient="records")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/high-risk")
async def get_high_risk_customers(db: Session = Depends(get_db),
                                   threshold: float = 0.7,
                                   limit: int = 50,
                                   current_user=Depends(get_current_user)):
    from db.models import Customer
    customers = (
        db.query(Customer)
        .filter(Customer.churn_probability >= threshold, Customer.is_churned == False)
        .order_by(Customer.churn_probability.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": c.id,
            "customer_number": c.customer_number,
            "full_name": c.full_name,
            "churn_probability": c.churn_probability,
            "branch_id": c.branch_id,
        }
        for c in customers
    ]
