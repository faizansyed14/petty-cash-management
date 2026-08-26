from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.deps import DbSession, CurrentUser
from app.schemas.auth import LoginRequest, LoginResponse, UserOut
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse, summary="Login with email and password")
def login(payload: LoginRequest, db: DbSession):
    result = auth_service.authenticate(db, payload.email, payload.password)
    if not result:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return result


@router.post("/token", response_model=LoginResponse, summary="OAuth2 password form login", include_in_schema=False)
def login_form(db: DbSession, form: OAuth2PasswordRequestForm = Depends()):
    result = auth_service.authenticate(db, form.username, form.password)
    if not result:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return result


@router.get("/me", response_model=UserOut, summary="Current user profile")
def me(user: CurrentUser):
    return user
