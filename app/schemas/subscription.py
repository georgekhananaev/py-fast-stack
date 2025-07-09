import json
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator


class InterestsValidatorMixin:
    """Mixin for handling interests field validation."""

    @field_validator('interests')
    def validate_interests(cls, v) -> str | None:
        """Convert interests list to JSON string for storage."""
        if v is None:
            return None
        return json.dumps(v)


class SubscriptionBase(InterestsValidatorMixin, BaseModel):
    """Base subscription schema."""
    email: EmailStr
    name: str
    company: str | None = None
    interests: list[str] | None = None


class SubscriptionCreate(SubscriptionBase):
    """Schema for creating a subscription."""
    pass


class SubscriptionUpdate(InterestsValidatorMixin, BaseModel):
    """Schema for updating a subscription."""
    name: str | None = None
    company: str | None = None
    interests: list[str] | None = None
    is_active: bool | None = None


class SubscriptionInDB(SubscriptionBase):
    """Schema for subscription in database."""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator('interests', mode='before')
    def parse_interests(cls, v) -> list[str] | None:
        """Parse interests JSON string back to list."""
        if v is None or v == "":
            return None
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return None
        return v


class Subscription(SubscriptionInDB):
    """Public subscription schema."""
    pass
