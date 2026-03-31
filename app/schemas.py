from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class StudentRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    institution_id: int
    full_name: str = Field(min_length=2, max_length=255)
    age: Optional[int] = Field(default=None, ge=5, le=120)


class StudentLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class SdmaAdminLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class SdmaAdminLoginResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'
    email: EmailStr
    display_name: str


class SignupInitiateRequest(BaseModel):
    institution_id: int
    email: EmailStr
    id_card_number: str = Field(min_length=2, max_length=128)
    full_name: str = Field(min_length=2, max_length=255)
    age: int = Field(ge=5, le=120)


class SignupInitiateResponse(BaseModel):
    message: str
    verification_token: Optional[str] = None


class VerifyEmailRequest(BaseModel):
    token: str = Field(min_length=8, max_length=16)


class CompleteSignupRequest(BaseModel):
    token: str = Field(min_length=8, max_length=16)
    password: str = Field(min_length=8, max_length=128)


class Token(BaseModel):
    access_token: str
    token_type: str = 'bearer'


class ForgotPasswordRequest(BaseModel):
    email: EmailStr
    id_card_number: str = Field(min_length=2, max_length=128)


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=8, max_length=16)
    new_password: str = Field(min_length=8, max_length=128)


class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str]
    role: str
    institution_id: int
    email_verified_at: Optional[datetime]

    model_config = {'from_attributes': True}


class MessageResponse(BaseModel):
    message: str


class RegisterResponse(BaseModel):
    message: str
    user_id: int


class ForgotPasswordResponse(BaseModel):
    message: str
    reset_token: Optional[str] = None


class SOSTriggerRequest(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    location_text: Optional[str] = Field(default=None, max_length=255)
    accuracy_meters: Optional[float] = Field(default=None, ge=0)


class SOSTriggerResponse(BaseModel):
    message: str
    event_id: int
    created_at: datetime


class SOSActiveStudentDetails(BaseModel):
    user_id: int
    full_name: Optional[str] = None
    email: EmailStr
    id_card_number: Optional[str] = None


class SOSActiveEventOut(BaseModel):
    event_id: int
    status: str
    latitude: float
    longitude: float
    location_text: Optional[str] = None
    accuracy_meters: Optional[float] = None
    created_at: datetime
    student: SOSActiveStudentDetails


class SOSActiveEventsResponse(BaseModel):
    events: list[SOSActiveEventOut]


class SOSResolvedEventsResponse(BaseModel):
    events: list[SOSActiveEventOut]


class SOSResolveCaseResponse(BaseModel):
    message: str
    event: SOSActiveEventOut
