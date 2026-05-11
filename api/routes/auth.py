from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from db.connection import get_db
from db.models import UserRole
from services.auth_service import AuthService
from config.security import decode_token
from api.middleware.rate_limit import limiter

router = APIRouter(prefix="/auth", tags=["Authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str
    role: UserRole = UserRole.BUSINESS_ANALYST
    branch_id: int = None


class PreferencesRequest(BaseModel):
    language: str = None
    theme: str = None


@router.post("/login")
@limiter.limit("10/minute")
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(),
                db: Session = Depends(get_db)):
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    result = AuthService.authenticate(db, form_data.username, form_data.password, ip, ua)
    if not result:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Incorrect username or password")
    return result


@router.post("/register", status_code=201)
@limiter.limit("5/minute")
async def register(request: Request, body: RegisterRequest, db: Session = Depends(get_db)):
    try:
        user = AuthService.create_user(
            db, body.username, body.email, body.password,
            body.full_name, body.role, body.branch_id
        )
        return {"id": user.id, "username": user.username, "email": user.email, "role": user.role}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/logout")
async def logout(request: Request, token: str = Depends(oauth2_scheme),
                 db: Session = Depends(get_db)):
    payload = decode_token(token)
    if payload:
        AuthService.logout(db, token, int(payload["sub"]))
    return {"message": "Logged out successfully"}


@router.put("/preferences")
async def update_preferences(body: PreferencesRequest, token: str = Depends(oauth2_scheme),
                              db: Session = Depends(get_db)):
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    AuthService.update_preferences(db, int(payload["sub"]), body.language, body.theme)
    return {"message": "Preferences updated"}


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    from db.models import User
    user = db.query(User).filter_by(id=int(payload["sub"]), is_active=True).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user
