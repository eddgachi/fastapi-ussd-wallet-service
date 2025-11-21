from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class TransactionResponse(BaseModel):
    id: str
    user_id: str
    loan_id: Optional[str] = None
    type: str
    amount: float
    status: str
    description: Optional[str] = None
    mpesa_receipt: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
