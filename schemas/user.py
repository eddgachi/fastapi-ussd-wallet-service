from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class UserBase(BaseModel):
    phone_number: str
    national_id: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    first_name: Optional[str]
    last_name: Optional[str]
    national_id: Optional[str]


class UserResponse(UserBase):
    id: str
    credit_score: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
