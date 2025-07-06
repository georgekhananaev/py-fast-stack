from typing import Optional, List
from pydantic import BaseModel, EmailStr, validator
from datetime import datetime
import json


class SubscriptionBase(BaseModel):
    """Base subscription schema."""
    email: EmailStr
    name: str
    company: Optional[str] = None
    interests: Optional[List[str]] = None

    @validator('interests')
    def validate_interests(cls, v):
        """Convert interests list to JSON string for storage."""
        if v is None:
            return None
        return json.dumps(v)


class SubscriptionCreate(SubscriptionBase):
    """Schema for creating a subscription."""
    pass


class SubscriptionUpdate(BaseModel):
    """Schema for updating a subscription."""
    name: Optional[str] = None
    company: Optional[str] = None
    interests: Optional[List[str]] = None
    is_active: Optional[bool] = None

    @validator('interests')
    def validate_interests(cls, v):
        """Convert interests list to JSON string for storage."""
        if v is None:
            return None
        return json.dumps(v)


class SubscriptionInDB(SubscriptionBase):
    """Schema for subscription in database."""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @validator('interests', pre=True)
    def parse_interests(cls, v):
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