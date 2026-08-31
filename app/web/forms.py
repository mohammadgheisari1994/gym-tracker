"""Validated form-input models for the web layer.

These parse and validate raw request data. Business rules (uniqueness,
credential checks) live in the service layer.
"""

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from app.i18n import SUPPORTED_LANGUAGES

_MIN_PASSWORD_LENGTH = 8


class SignupForm(BaseModel):
    email: EmailStr
    display_name: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=_MIN_PASSWORD_LENGTH, max_length=128)
    password_confirm: str
    preferred_language: str = "en"

    @field_validator("preferred_language")
    @classmethod
    def _known_language(cls, value: str) -> str:
        return value if value in SUPPORTED_LANGUAGES else "en"

    @model_validator(mode="after")
    def _passwords_match(self) -> "SignupForm":
        if self.password != self.password_confirm:
            raise ValueError("passwords do not match")
        return self


class LoginForm(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class ProfileForm(BaseModel):
    display_name: str = Field(min_length=1, max_length=80)
    preferred_language: str = "en"

    @field_validator("preferred_language")
    @classmethod
    def _known_language(cls, value: str) -> str:
        return value if value in SUPPORTED_LANGUAGES else "en"


class PasswordChangeForm(BaseModel):
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=_MIN_PASSWORD_LENGTH, max_length=128)
    new_password_confirm: str

    @model_validator(mode="after")
    def _passwords_match(self) -> "PasswordChangeForm":
        if self.new_password != self.new_password_confirm:
            raise ValueError("passwords do not match")
        return self
