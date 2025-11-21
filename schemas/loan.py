from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class LoanStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    DISBURSED = "disbursed"
    REPAID = "repaid"
    DEFAULTED = "defaulted"


class LoanBase(BaseModel):
    amount: float
    term_days: int
    purpose: Optional[str] = "General"


class LoanCreate(LoanBase):
    user_id: str


class LoanUpdate(BaseModel):
    status: Optional[LoanStatus]
    interest_rate: Optional[float]


class LoanResponse(LoanBase):
    id: str
    user_id: str
    interest_rate: float
    status: LoanStatus
    amount_due: Optional[float]
    application_date: datetime
    approved_date: Optional[datetime]
    disbursed_date: Optional[datetime]
    due_date: Optional[datetime]

    class Config:
        from_attributes = True


class LoanAdminResponse(LoanResponse):
    repaid_date: Optional[datetime] = None
