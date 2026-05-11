"""
IntelliBank FastAPI REST Layer
Exposes ML models as production-grade REST endpoints
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from api.middleware.rate_limit import limiter, rate_limit_handler
from api.routes import auth, fraud, churn, forecast, nlp
from config.settings import settings
from config.security import SECURITY_HEADERS
from db.connection import init_db
from services.scheduler import start_scheduler, stop_scheduler
from services.alert_service import register_ws_client, unregister_ws_client, broadcast_alert

logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL))
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    start_scheduler()
    logger.info("IntelliBank API started.")
    yield
    stop_scheduler()
    logger.info("IntelliBank API stopped.")


app = FastAPI(
    title="IntelliBank API",
    description="AI-Powered Banking Data Analyst REST API",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# Rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    for header, value in SECURITY_HEADERS.items():
        response.headers[header] = value
    return response


# Routes
app.include_router(auth.router, prefix="/api")
app.include_router(fraud.router, prefix="/api")
app.include_router(churn.router, prefix="/api")
app.include_router(forecast.router, prefix="/api")
app.include_router(nlp.router, prefix="/api")


# WebSocket for real-time fraud alerts
@app.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    await websocket.accept()
    register_ws_client(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        unregister_ws_client(websocket)


@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/api/audit-logs")
async def audit_logs(limit: int = 50, action: str = None,
                      request: Request = None):
    from db.connection import SessionLocal
    from services.auth_service import AuditService
    db = SessionLocal()
    logs = AuditService.get_logs(db, action=action, limit=limit)
    db.close()
    return [
        {
            "id": l.id,
            "user_id": l.user_id,
            "action": l.action,
            "resource": l.resource,
            "ip_address": l.ip_address,
            "is_success": l.is_success,
            "created_at": str(l.created_at),
        }
        for l in logs
    ]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host=settings.API_HOST,
                port=settings.API_PORT, reload=settings.DEBUG)
