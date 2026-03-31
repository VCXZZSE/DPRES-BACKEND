from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import and_, select
from sqlalchemy.orm import Session
import secrets

from app.core.email import (
    send_welcome_onboarding_email,
    send_password_changed_alert_email,
    send_password_reset_token_email,
    send_signup_verification_email,
)
from app.core.security import (
    create_access_token,
    decode_token,
    extract_email_domain,
    hash_password,
    verify_password,
)
from app.database import get_db
from app.models import Institution, PasswordReset, SignupVerification, StudentDirectory, User, UserRole
from app.schemas import (
    CompleteSignupRequest,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    MessageResponse,
    SignupInitiateRequest,
    SignupInitiateResponse,
    RegisterResponse,
    ResetPasswordRequest,
    SdmaAdminLoginRequest,
    SdmaAdminLoginResponse,
    StudentLogin,
    StudentRegister,
    Token,
    UserOut,
    VerifyEmailRequest,
)

router = APIRouter(prefix='/api/auth', tags=['auth'])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/api/auth/login-student')

# Import limiter from main for rate limiting decorators
from app.main import limiter


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _normalize_name(full_name: str) -> str:
    return ' '.join(full_name.strip().split())


def _validate_institution_email_domain(email: str, institution: Institution) -> None:
    email_domain = extract_email_domain(email)

    blocked_public_domains = {
        'gmail.com',
        'googlemail.com',
    }
    if email_domain in blocked_public_domains:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Personal Gmail addresses are not allowed. Please use your education or workplace email.',
        )


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    try:
        payload = decode_token(token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid token') from exc
    if payload.get('type') != 'access':
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid token type')

    user_id_raw = payload.get('sub')
    try:
        user_id = int(user_id_raw)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid token subject') from exc

    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='User not found or inactive')
    return user


def get_current_sdma_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.SDMA_ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='SDMA admin access required')
    return current_user


@router.get('/ping')
def ping_auth() -> dict[str, str]:
    return {'status': 'auth-router-ready'}


@router.post('/register-student', response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register_student(payload: StudentRegister, db: Session = Depends(get_db)) -> RegisterResponse:
    email = _normalize_email(payload.email)

    existing_user = db.scalar(select(User).where(User.email == email))
    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Account already exists')

    institution = db.get(Institution, payload.institution_id)
    if not institution:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Institution not found')

    _validate_institution_email_domain(email, institution)

    user = User(
        email=email,
        full_name=payload.full_name.strip(),
        password_hash=hash_password(payload.password),
        role=UserRole.STUDENT,
        institution_id=institution.id,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return RegisterResponse(message='Student account created successfully', user_id=user.id)


@router.post('/signup-initiate', response_model=SignupInitiateResponse)
@limiter.limit("5/minute")
def signup_initiate(payload: SignupInitiateRequest, db: Session = Depends(get_db)) -> SignupInitiateResponse:
    now = datetime.now(timezone.utc)
    email = _normalize_email(payload.email)
    normalized_name = _normalize_name(payload.full_name)

    institution = db.get(Institution, payload.institution_id)
    if not institution:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Institution not found')

    _validate_institution_email_domain(email, institution)

    existing_user = db.scalar(select(User).where(User.email == email))
    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Account already exists')

    db.query(SignupVerification).filter(
        and_(
            SignupVerification.email == email,
            SignupVerification.used_at.is_(None),
        )
    ).update({'used_at': now}, synchronize_session=False)

    token = secrets.token_urlsafe(32)
    expires_at = now + timedelta(minutes=15)
    verification = SignupVerification(
        institution_id=payload.institution_id,
        email=email,
        id_card_number=payload.id_card_number.strip(),
        full_name=normalized_name,
        age=payload.age,
        token=token,
        expires_at=expires_at,
    )
    db.add(verification)
    db.commit()

    email_sent = False
    try:
        email_sent = send_signup_verification_email(email, token)
    except Exception:
        email_sent = False

    return SignupInitiateResponse(
        message=(
            'Verification email sent. Please verify and complete signup.'
            if email_sent
            else 'Verification token generated. Please verify and complete signup.'
        ),
    )


@router.post('/verify-email', response_model=MessageResponse)
def verify_email(payload: VerifyEmailRequest, db: Session = Depends(get_db)) -> MessageResponse:
    now = datetime.now(timezone.utc)
    verification = db.scalar(
        select(SignupVerification).where(
            and_(
                SignupVerification.token == payload.token,
                SignupVerification.used_at.is_(None),
                SignupVerification.expires_at > now,
            )
        )
    )
    if not verification:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid or expired verification token')

    if verification.email_verified_at is None:
        verification.email_verified_at = now
        db.commit()

    return MessageResponse(message='Email verified successfully')


@router.post('/complete-signup', response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def complete_signup(payload: CompleteSignupRequest, db: Session = Depends(get_db)) -> RegisterResponse:
    now = datetime.now(timezone.utc)
    verification = db.scalar(
        select(SignupVerification).where(
            and_(
                SignupVerification.token == payload.token,
                SignupVerification.used_at.is_(None),
                SignupVerification.expires_at > now,
            )
        )
    )
    if not verification:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid or expired signup token')

    if verification.email_verified_at is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Email must be verified before signup completion')

    institution = db.get(Institution, verification.institution_id)
    if not institution:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Institution not found')

    _validate_institution_email_domain(verification.email, institution)

    existing_user = db.scalar(select(User).where(User.email == verification.email))
    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Account already exists')

    existing_id_card = db.scalar(select(User).where(User.id_card_number == verification.id_card_number))
    if existing_id_card:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='ID card already linked to another account')

    user = User(
        email=verification.email,
        id_card_number=verification.id_card_number,
        full_name=verification.full_name,
        password_hash=hash_password(payload.password),
        role=UserRole.STUDENT,
        institution_id=verification.institution_id,
        is_active=True,
        email_verified_at=verification.email_verified_at,
    )

    directory_entry = db.scalar(
        select(StudentDirectory).where(
            and_(
                StudentDirectory.email == verification.email,
                StudentDirectory.id_card_number == verification.id_card_number,
            )
        )
    )
    if not directory_entry:
        db.add(
            StudentDirectory(
                institution_id=verification.institution_id,
                email=verification.email,
                id_card_number=verification.id_card_number,
                full_name=verification.full_name,
                age=verification.age,
                is_active=True,
            )
        )

    verification.used_at = now
    db.add(user)
    db.commit()
    db.refresh(user)

    try:
        send_welcome_onboarding_email(user.email, user.full_name or 'User')
    except Exception:
        # Account creation is successful even if welcome email delivery fails.
        pass

    return RegisterResponse(message='Student account created successfully', user_id=user.id)


@router.post('/login-student', response_model=Token)
@limiter.limit("5/minute")
def login_student(payload: StudentLogin, db: Session = Depends(get_db)) -> Token:
    email = _normalize_email(payload.email)
    user = db.scalar(select(User).where(and_(User.email == email, User.role == UserRole.STUDENT)))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid email or password')

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Account is inactive')

    if user.email_verified_at is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Email is not verified')

    access_token = create_access_token(subject=str(user.id))
    return Token(access_token=access_token)


@router.post('/login-sdma-admin', response_model=SdmaAdminLoginResponse)
@limiter.limit("5/minute")
def login_sdma_admin(payload: SdmaAdminLoginRequest, db: Session = Depends(get_db)) -> SdmaAdminLoginResponse:
    email = _normalize_email(payload.email)

    user = db.scalar(select(User).where(and_(User.email == email, User.role == UserRole.SDMA_ADMIN)))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid email or password')

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Account is inactive')

    access_token = create_access_token(subject=str(user.id))

    return SdmaAdminLoginResponse(
        access_token=access_token,
        email=user.email,
        display_name=user.full_name or 'SDMA Admin',
    )


@router.post('/forgot-password', response_model=ForgotPasswordResponse)
@limiter.limit("5/minute")
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)) -> ForgotPasswordResponse:
    email = _normalize_email(payload.email)
    id_card_number = payload.id_card_number.strip()

    user = db.scalar(
        select(User).where(
            and_(
                User.email == email,
                User.id_card_number == id_card_number,
                User.role == UserRole.STUDENT,
            )
        )
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Invalid email or ID card combination',
        )

    directory_entry = db.scalar(
        select(StudentDirectory).where(
            and_(
                StudentDirectory.email == email,
                StudentDirectory.id_card_number == id_card_number,
                StudentDirectory.is_active.is_(True),
            )
        )
    )
    if not directory_entry:
        latest_age = db.scalar(
            select(SignupVerification.age)
            .where(
                and_(
                    SignupVerification.email == email,
                    SignupVerification.id_card_number == id_card_number,
                )
            )
            .order_by(SignupVerification.created_at.desc())
            .limit(1)
        )
        db.add(
            StudentDirectory(
                institution_id=user.institution_id,
                email=user.email,
                id_card_number=user.id_card_number or id_card_number,
                full_name=user.full_name or 'Student',
                age=latest_age or 20,
                is_active=True,
            )
        )
        db.commit()

    db.query(PasswordReset).filter(
        and_(
            PasswordReset.user_id == user.id,
            PasswordReset.used_at.is_(None),
        )
    ).update({'used_at': datetime.now(timezone.utc)}, synchronize_session=False)

    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)

    db.add(
        PasswordReset(
            user_id=user.id,
            token=token,
            expires_at=expires_at,
        )
    )
    db.commit()

    email_sent = False
    try:
        email_sent = send_password_reset_token_email(email, token)
    except Exception:
        email_sent = False

    if not email_sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Unable to send reset email. Please try again shortly.',
        )

    return ForgotPasswordResponse(
        message='A reset verification token has been sent to your email.',
        reset_token=None,
    )


@router.post('/reset-password', response_model=MessageResponse)
@limiter.limit("5/minute")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)) -> MessageResponse:
    now = datetime.now(timezone.utc)
    reset_entry = db.scalar(
        select(PasswordReset).where(
            and_(
                PasswordReset.token == payload.token,
                PasswordReset.used_at.is_(None),
                PasswordReset.expires_at > now,
            )
        )
    )

    if not reset_entry:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid or expired reset token')

    user = db.get(User, reset_entry.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')

    user.password_hash = hash_password(payload.new_password)
    reset_entry.used_at = now
    db.commit()

    try:
        send_password_changed_alert_email(user.email, changed_at_utc=now)
    except Exception:
        # Password has already been changed; do not roll back on notification failures.
        pass

    return MessageResponse(message='Password has been reset successfully')


@router.get('/me', response_model=UserOut)
def me(current_user: User = Depends(get_current_user)) -> UserOut:
    return UserOut(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role.value,
        institution_id=current_user.institution_id,
        email_verified_at=current_user.email_verified_at,
    )


@router.get('/me-sdma-admin', response_model=UserOut)
def me_sdma_admin(current_admin: User = Depends(get_current_sdma_admin)) -> UserOut:
    return UserOut(
        id=current_admin.id,
        email=current_admin.email,
        full_name=current_admin.full_name,
        role=current_admin.role.value,
        institution_id=current_admin.institution_id,
        email_verified_at=current_admin.email_verified_at,
    )
