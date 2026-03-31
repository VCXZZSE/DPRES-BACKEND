import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserRole(str, enum.Enum):
    STUDENT = 'student'
    INSTITUTION_ADMIN = 'institution_admin'
    SDMA_ADMIN = 'sdma_admin'


class Institution(Base):
    __tablename__ = 'institutions'

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    institution_type: Mapped[str] = mapped_column(String(20), nullable=False)  # school | college
    district: Mapped[Optional[str]] = mapped_column(String(100))
    state: Mapped[Optional[str]] = mapped_column(String(100))

    # Key for your "college mail only" rule
    # Example: ['stxaviers.edu.in', 'jadavpuruniversity.in']
    allowed_domains: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    users: Mapped[list['User']] = relationship(back_populates='institution')


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    id_card_number: Mapped[Optional[str]] = mapped_column(String(128), unique=True, index=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(255))

    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name='user_role'), default=UserRole.STUDENT)

    institution_id: Mapped[int] = mapped_column(ForeignKey('institutions.id', ondelete='RESTRICT'), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    email_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    institution: Mapped[Institution] = relationship(back_populates='users')


class StudentDirectory(Base):
    __tablename__ = 'student_directory'

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    institution_id: Mapped[int] = mapped_column(ForeignKey('institutions.id', ondelete='RESTRICT'), nullable=False)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    id_card_number: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    age: Mapped[int] = mapped_column(nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class SignupVerification(Base):
    __tablename__ = 'signup_verifications'

    id: Mapped[int] = mapped_column(primary_key=True)
    institution_id: Mapped[int] = mapped_column(ForeignKey('institutions.id', ondelete='RESTRICT'), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    id_card_number: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    age: Mapped[int] = mapped_column(nullable=False)
    token: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    email_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EmailVerification(Base):
    __tablename__ = 'email_verifications'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    token: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PasswordReset(Base):
    __tablename__ = 'password_resets'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    token: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SessionToken(Base):
    __tablename__ = 'sessions'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    refresh_token_hash: Mapped[str] = mapped_column(Text, nullable=False)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500))
    ip_address: Mapped[Optional[str]] = mapped_column(String(64))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SOSEvent(Base):
    __tablename__ = 'sos_events'

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    latitude: Mapped[float] = mapped_column(nullable=False)
    longitude: Mapped[float] = mapped_column(nullable=False)
    location_text: Mapped[Optional[str]] = mapped_column(String(255))
    accuracy_meters: Mapped[Optional[float]] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default='active')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship()


Index('ix_email_verifications_user_token', EmailVerification.user_id, EmailVerification.token)
Index('ix_password_resets_user_token', PasswordReset.user_id, PasswordReset.token)
Index('ix_student_directory_lookup', StudentDirectory.institution_id, StudentDirectory.email, StudentDirectory.id_card_number)
Index('ix_signup_verification_lookup', SignupVerification.email, SignupVerification.id_card_number, SignupVerification.used_at)
