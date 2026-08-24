import threading
import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
    OAuth2PasswordRequestForm,
)
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
    UserResponse,
)
from app.schemas.common import ApiResponse, success_response

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])
bearer_scheme = HTTPBearer(auto_error=False)
_login_attempts: dict[str, list[float]] = {}
_login_attempts_lock = threading.Lock()


def _check_login_rate_limit(username: str) -> None:
    now = time.time()
    window = 60
    max_attempts = 5
    with _login_attempts_lock:
        attempts = [ts for ts in _login_attempts.get(username, []) if now - ts < window]
        if len(attempts) >= max_attempts:
            raise HTTPException(status_code=429, detail="登录尝试过于频繁，请稍后再试")
        attempts.append(now)
        _login_attempts[username] = attempts


def get_current_user_required(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    user = _resolve_token_user(credentials, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Optional[User]:
    return _resolve_token_user(credentials, db)


def _resolve_token_user(
    credentials: Optional[HTTPAuthorizationCredentials],
    db: Session,
) -> Optional[User]:
    if credentials is None:
        return None
    user_id = decode_access_token(credentials.credentials)
    if not user_id:
        return None
    return db.query(User).filter(User.id == user_id, User.is_active.is_(True)).first()


def _authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    user = db.query(User).filter(User.name == username).first()
    if not user or not user.is_active or not user.hashed_password or not verify_password(password, user.hashed_password):
        return None
    return user


@router.post("/register", response_model=ApiResponse[RegisterResponse])
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    name = req.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="用户名不能为空")
    existing = db.query(User).filter(User.name == name).first()
    if existing:
        raise HTTPException(status_code=409, detail="用户名已存在")

    user = User(name=name, hashed_password=hash_password(req.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return success_response(RegisterResponse.model_validate(user))


@router.post("/login", response_model=ApiResponse[LoginResponse])
def login(req: LoginRequest, db: Session = Depends(get_db)):
    _check_login_rate_limit(req.username)
    user = _authenticate_user(db, req.username, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    token = create_access_token(user.id)
    return success_response(
        LoginResponse(
            access_token=token,
            token_type="bearer",
            user=UserResponse.model_validate(user),
        )
    )


@router.post("/token", response_model=ApiResponse[LoginResponse])
def login_form(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    _check_login_rate_limit(form.username)
    user = _authenticate_user(db, form.username, form.password)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    token = create_access_token(user.id)
    return success_response(
        LoginResponse(
            access_token=token,
            token_type="bearer",
            user=UserResponse.model_validate(user),
        )
    )


@router.get("/me", response_model=ApiResponse[UserResponse])
def me(current_user: User = Depends(get_current_user_required)):
    return success_response(UserResponse.model_validate(current_user))


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user_required)):
    return {"success": True, "data": None, "error": None}
