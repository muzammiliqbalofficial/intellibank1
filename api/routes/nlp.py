from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from db.connection import get_db
from api.middleware.rate_limit import limiter
from api.routes.auth import get_current_user
from services.nlp_service import execute_nlp_query, get_suggested_queries
from db.models import NLPQuery

router = APIRouter(prefix="/nlp", tags=["NLP Query"])


class NLPQueryRequest(BaseModel):
    query: str
    language: str = "auto"


@router.post("/query")
@limiter.limit("20/minute")
async def run_nlp_query(request: Request, body: NLPQueryRequest,
                         db: Session = Depends(get_db),
                         current_user=Depends(get_current_user)):
    result = execute_nlp_query(body.query, db)

    # Persist query log
    log = NLPQuery(
        user_id=current_user.id,
        original_query=result["original_query"],
        detected_language=result.get("detected_language"),
        translated_query=result.get("translated_query"),
        generated_sql=result.get("generated_sql"),
        query_result=result.get("query_result"),
        result_row_count=result.get("result_row_count", 0),
        execution_time_ms=result.get("execution_time_ms"),
        is_successful=result.get("is_successful", False),
        error_message=result.get("error_message"),
    )
    db.add(log)
    db.commit()

    return result


@router.get("/suggestions")
async def get_suggestions(language: str = "en",
                           current_user=Depends(get_current_user)):
    return {"suggestions": get_suggested_queries(language)}


@router.get("/history")
async def query_history(db: Session = Depends(get_db),
                         limit: int = 20,
                         current_user=Depends(get_current_user)):
    logs = (
        db.query(NLPQuery)
        .filter_by(user_id=current_user.id)
        .order_by(NLPQuery.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": l.id,
            "query": l.original_query,
            "language": l.detected_language,
            "row_count": l.result_row_count,
            "success": l.is_successful,
            "created_at": str(l.created_at),
        }
        for l in logs
    ]
