"""Validated form-input models for the web layer.

These parse and validate raw request data. Business rules (uniqueness,
credential checks) live in the service layer.
"""

from datetime import date
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from app.i18n import SUPPORTED_LANGUAGES
from app.models import MuscleGroup, SetType, WeightUnit

_MIN_PASSWORD_LENGTH = 8


def _enum_or(enum_cls: type[Enum], default: Enum, value: object) -> object:
    """Map an unrecognised submitted value onto ``default``."""
    if isinstance(value, str) and value not in enum_cls._value2member_map_:
        return default
    return value


def _blank_to_none(value: object) -> object:
    if isinstance(value, str) and value.strip() == "":
        return None
    return value


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
    weight_unit: WeightUnit = WeightUnit.KG

    @field_validator("preferred_language")
    @classmethod
    def _known_language(cls, value: str) -> str:
        return value if value in SUPPORTED_LANGUAGES else "en"

    @field_validator("weight_unit", mode="before")
    @classmethod
    def _known_weight_unit(cls, value: object) -> object:
        return _enum_or(WeightUnit, WeightUnit.KG, value)


class ExerciseForm(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    muscle_group: MuscleGroup = MuscleGroup.OTHER
    notes: str = Field(default="", max_length=2000)

    @field_validator("muscle_group", mode="before")
    @classmethod
    def _known_muscle_group(cls, value: object) -> object:
        return _enum_or(MuscleGroup, MuscleGroup.OTHER, value)


class PasswordChangeForm(BaseModel):
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=_MIN_PASSWORD_LENGTH, max_length=128)
    new_password_confirm: str

    @model_validator(mode="after")
    def _passwords_match(self) -> "PasswordChangeForm":
        if self.new_password != self.new_password_confirm:
            raise ValueError("passwords do not match")
        return self


class WorkoutForm(BaseModel):
    performed_on: date
    title: str = Field(default="", max_length=120)
    notes: str = Field(default="", max_length=2000)


class SetForm(BaseModel):
    weight: Decimal | None = Field(default=None, ge=0, le=10000, decimal_places=2)
    reps: int = Field(ge=1, le=1000)
    set_type: SetType = SetType.NORMAL
    rpe: Decimal | None = Field(default=None, ge=1, le=10, decimal_places=1)

    @field_validator("set_type", mode="before")
    @classmethod
    def _known_set_type(cls, value: object) -> object:
        return _enum_or(SetType, SetType.NORMAL, value)

    @field_validator("weight", "rpe", mode="before")
    @classmethod
    def _empty_is_none(cls, value: object) -> object:
        return _blank_to_none(value)
