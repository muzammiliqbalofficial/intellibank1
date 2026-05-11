from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from db.connection import get_db
from api.middleware.rate_limit import limiter
from api.routes.auth import get_current_user

router = APIRouter(prefix="/fraud", tags=["Fraud Detection"])


class TransactionInput(BaseModel):
    amount: float
    merchant_category: Optional[str] = "other"
    transaction_type: Optional[str] = "debit"
    location: Optional[str] = None
    hour: Optional[int] = 12
    day_of_week: Optional[int] = 1
    is_weekend: Optional[int] = 0


class BatchTransactionInput(BaseModel):
    transactions: List[dict]


@router.post("/predict")
@limiter.limit("30/minute")
async def predict_fraud(request: Request, transaction: TransactionInput,
                         db: Session = Depends(get_db),
                         current_user=Depends(get_current_user)):
    from ml.fraud.predict import predict_single
    try:
        result = predict_single(transaction.dict())
        from services.alert_service import send_fraud_alert
        from config.settings import settings
        if result["fraud_probability"] >= settings.FRAUD_ALERT_THRESHOLD:
            send_fraud_alert(
                transaction_id=0,
                fraud_score=result["fraud_probability"],
                amount=transaction.amount,
                account_number="N/A",
                top_features=result.get("top_features"),
            )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predict/batch")
@limiter.limit("5/minute")
async def predict_fraud_batch(request: Request, body: BatchTransactionInput,
                               current_user=Depends(get_current_user)):
    import pandas as pd
    from ml.fraud.predict import predict_batch
    try:
        df = pd.DataFrame(body.transactions)
        result_df = predict_batch(df)
        return {"count": len(result_df), "results": result_df.to_dict(orient="records")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts")
async def get_fraud_alerts(db: Session = Depends(get_db),
                            resolved: Optional[bool] = None,
                            limit: int = 50,
                            current_user=Depends(get_current_user)):
    from db.models import FraudAlert
    query = db.query(FraudAlert)
    if resolved is not None:
        query = query.filter_by(is_resolved=resolved)
    alerts = query.order_by(FraudAlert.created_at.desc()).limit(limit).all()
    return [
        {
            "id": a.id,
            "transaction_id": a.transaction_id,
            "fraud_score": a.fraud_score,
            "is_resolved": a.is_resolved,
            "created_at": str(a.created_at),
        }
        for a in alerts
    ]


@router.put("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: int, notes: str = "",
                         db: Session = Depends(get_db),
                         current_user=Depends(get_current_user)):
    from db.models import FraudAlert
    from datetime import datetime
    alert = db.query(FraudAlert).filter_by(id=alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.is_resolved = True
    alert.resolved_by = current_user.id
    alert.resolved_at = datetime.utcnow()
    alert.notes = notes
    db.commit()
    return {"message": "Alert resolved", "alert_id": alert_id}
