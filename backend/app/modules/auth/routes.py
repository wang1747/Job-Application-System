import random
import re
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
from app.core.email import send_email
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import (
    ChangeEmailRequest,
    ChangeEmailSendCodeRequest,
    ChangePasswordRequest,
    LoginRequest,
    LoginResponse,
    ProfileUpdateRequest,
    RegisterRequest,
    RegisterResponse,
    ResetPasswordRequest,
    SendCodeRequest,
    UserResponse,
)
from app.schemas.common import ApiResponse, success_response

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])
bearer_scheme = HTTPBearer(auto_error=False)
_login_attempts: dict[str, list[float]] = {}
_login_attempts_lock = threading.Lock()

# 验证码存储：key = "account:email" 或 "change-email:{user_id}:{email}"
# -> (code, expire_ts, last_send_ts)
_verification_codes: dict[str, tuple[str, float, float]] = {}
_verification_codes_lock = threading.Lock()

_CODE_TTL = 600          # 验证码有效期 10 分钟
_CODE_RESEND_INTERVAL = 60  # 同账号重发间隔 60 秒

# 账号格式校验：邮箱
_EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def _classify_account(account: str):
    """识别账号类型，返回 (kind, value, display_name)。

    kind ∈ {"email", ""}；"" 表示格式不合法。
    display_name 用于填充用户显示名（邮箱取 @ 前部分）。
    """
    value = account.strip()
    if _EMAIL_RE.match(value):
        return "email", value, value.split("@", 1)[0]
    return "", "", ""


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


def _issue_code(key: str, target_email: str, subject: str, body_tpl: str) -> None:
    """生成验证码并通过 SMTP 发送，成功后写入存储（含重发间隔限制）。"""
    now = time.time()
    with _verification_codes_lock:
        existing = _verification_codes.get(key)
        if existing and now - existing[2] < _CODE_RESEND_INTERVAL:
            raise HTTPException(status_code=429, detail="发送过于频繁，请稍后再试")

    code = f"{random.randint(0, 999999):06d}"
    expire = now + _CODE_TTL

    try:
        send_email(target_email, subject, body_tpl.format(code=code))
    except RuntimeError:
        raise HTTPException(status_code=503, detail="邮件服务未配置，请联系管理员")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"验证码发送失败：{e}")

    with _verification_codes_lock:
        _verification_codes[key] = (code, expire, now)


def _consume_code(key: str, code: str) -> None:
    """校验并一次性消费验证码，失败抛 HTTPException。"""
    code = (code or "").strip()
    with _verification_codes_lock:
        stored = _verification_codes.get(key)
        if not stored:
            raise HTTPException(status_code=400, detail="请先获取验证码")
        stored_code, expire, _ = stored
        if time.time() > expire:
            _verification_codes.pop(key, None)
            raise HTTPException(status_code=400, detail="验证码已过期，请重新获取")
        if stored_code != code:
            raise HTTPException(status_code=400, detail="验证码错误")
        _verification_codes.pop(key, None)  # 一次性使用


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


def _authenticate_user(db: Session, account: str, password: str) -> Optional[User]:
    """按账号登录：仅支持邮箱（邮箱即唯一身份）。"""
    email = (account or "").strip()
    if not _EMAIL_RE.match(email):
        return None
    user = db.query(User).filter(User.email == email).first()
    if not user or not user.is_active or not user.hashed_password or not verify_password(password, user.hashed_password):
        return None
    return user


@router.post("/register", response_model=ApiResponse[RegisterResponse])
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    account = req.account.strip()
    kind, value, auto_display = _classify_account(account)
    if not kind:
        raise HTTPException(status_code=400, detail="请输入正确的邮箱")

    # 用户称呼：填了用填的，没填则按账号自动生成（邮箱前缀）
    display_name = (req.name or "").strip()
    if not display_name:
        display_name = auto_display

    # 邮箱唯一性校验，避免重复注册
    existing = db.query(User).filter(User.email == value).first()
    if existing:
        raise HTTPException(status_code=409, detail="该邮箱已被注册")

    user = User(name=display_name, email=value, hashed_password=hash_password(req.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return success_response(RegisterResponse.model_validate(user))


@router.post("/login", response_model=ApiResponse[LoginResponse])
def login(req: LoginRequest, db: Session = Depends(get_db)):
    _check_login_rate_limit(req.username)
    user = _authenticate_user(db, req.username, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="邮箱或密码错误")

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
        raise HTTPException(status_code=401, detail="邮箱或密码错误")

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


@router.patch("/profile", response_model=ApiResponse[UserResponse])
def update_profile(
    req: ProfileUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    """更新个人资料（昵称）。"""
    current_user.name = req.name.strip()
    db.commit()
    db.refresh(current_user)
    return success_response(UserResponse.model_validate(current_user))


@router.post("/change-email/send-code", response_model=ApiResponse[dict])
def send_change_email_code(
    req: ChangeEmailSendCodeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    """换绑邮箱第一步：向新邮箱发送验证码。"""
    new_email = (req.new_email or "").strip().lower()
    if not _EMAIL_RE.match(new_email):
        raise HTTPException(status_code=400, detail="请输入正确的邮箱")
    if (current_user.email or "").strip().lower() == new_email:
        raise HTTPException(status_code=400, detail="新邮箱与当前一致")

    existing = db.query(User).filter(User.email == new_email).first()
    if existing and existing.id != current_user.id:
        raise HTTPException(status_code=409, detail="该邮箱已被其他账号使用")

    key = f"change-email:{current_user.id}:{new_email}"
    _issue_code(
        key,
        new_email,
        "OfferFlow 换绑邮箱验证码",
        "您的换绑邮箱验证码是 {code}，10 分钟内有效。如非本人操作请忽略本邮件。",
    )
    return success_response({"message": "验证码已发送", "email_masked": _mask_email(new_email)})


@router.post("/change-email", response_model=ApiResponse[UserResponse])
def change_email(
    req: ChangeEmailRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    """换绑邮箱第二步：校验新邮箱验证码后完成换绑。"""
    new_email = (req.new_email or "").strip().lower()
    if not _EMAIL_RE.match(new_email):
        raise HTTPException(status_code=400, detail="请输入正确的邮箱")
    if (current_user.email or "").strip().lower() == new_email:
        raise HTTPException(status_code=400, detail="新邮箱与当前一致")

    existing = db.query(User).filter(User.email == new_email).first()
    if existing and existing.id != current_user.id:
        raise HTTPException(status_code=409, detail="该邮箱已被其他账号使用")

    key = f"change-email:{current_user.id}:{new_email}"
    _consume_code(key, req.code)

    current_user.email = new_email
    db.commit()
    db.refresh(current_user)
    return success_response(UserResponse.model_validate(current_user))


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user_required)):
    return {"success": True, "data": None, "error": None}


@router.post("/change-password", response_model=ApiResponse[dict])
def change_password(
    req: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    """登录用户修改自己的密码：校验旧密码，新密码 bcrypt 加密存储。"""
    if not current_user.hashed_password or not verify_password(req.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="当前密码不正确")

    if req.new_password == req.old_password:
        raise HTTPException(status_code=400, detail="新密码不能与当前密码相同")

    current_user.hashed_password = hash_password(req.new_password)
    db.commit()
    return success_response({"message": "密码已修改，请使用新密码重新登录"})


def _mask_email(email: str) -> str:
    """邮箱脱敏：zhan***@qq.com，用于前端提示发到了哪个邮箱。"""
    local, _, domain = email.partition("@")
    if len(local) <= 2:
        head = local[:1]
    else:
        head = local[:2]
    return f"{head}***@{domain}"


def _resolve_account_and_email(db: Session, account: str, email: Optional[str]):
    """定位账号与收件邮箱（账号即邮箱）。

    返回 (user, target_email)。账号不存在返回 (None, None)。
    """
    kind, value, _ = _classify_account(account)
    if not kind:
        raise HTTPException(status_code=400, detail="请输入正确的邮箱")

    user = db.query(User).filter(User.email == value).first()
    return user, value


@router.post("/forgot-password/send-code", response_model=ApiResponse[dict])
def send_verification_code(req: SendCodeRequest, db: Session = Depends(get_db)):
    account = req.account.strip()
    user, target_email = _resolve_account_and_email(db, account, req.email)
    if not user:
        raise HTTPException(status_code=404, detail="该账号未注册")

    key = f"{account}:{target_email}"
    now = time.time()
    with _verification_codes_lock:
        existing = _verification_codes.get(key)
        if existing and now - existing[2] < _CODE_RESEND_INTERVAL:
            raise HTTPException(status_code=429, detail="发送过于频繁，请稍后再试")

    code = f"{random.randint(0, 999999):06d}"
    expire = now + _CODE_TTL

    try:
        send_email(
            target_email,
            "OfferFlow 找回密码验证码",
            f"您的验证码是 {code}，10 分钟内有效。如非本人操作请忽略本邮件。",
        )
    except RuntimeError:
        raise HTTPException(status_code=503, detail="邮件服务未配置，请联系管理员")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"验证码发送失败：{e}")

    with _verification_codes_lock:
        _verification_codes[key] = (code, expire, now)

    return success_response({"message": "验证码已发送", "email_masked": _mask_email(target_email)})


@router.post("/forgot-password/reset", response_model=ApiResponse[dict])
def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    account = req.account.strip()
    user, target_email = _resolve_account_and_email(db, account, req.email)
    if not user:
        raise HTTPException(status_code=404, detail="该账号未注册")

    key = f"{account}:{target_email}"
    code = req.code.strip()
    with _verification_codes_lock:
        stored = _verification_codes.get(key)
        if not stored:
            raise HTTPException(status_code=400, detail="请先获取验证码")
        stored_code, expire, _ = stored
        if time.time() > expire:
            _verification_codes.pop(key, None)
            raise HTTPException(status_code=400, detail="验证码已过期，请重新获取")
        if stored_code != code:
            raise HTTPException(status_code=400, detail="验证码错误")
        _verification_codes.pop(key, None)  # 一次性使用

    user.hashed_password = hash_password(req.new_password)
    db.commit()
    return success_response({"message": "密码已重置，请使用新密码登录"})
