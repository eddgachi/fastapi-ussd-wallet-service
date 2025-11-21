from datetime import datetime
from pydantic import BaseModel, ConfigDict

class WalletResponse(BaseModel):
    id: str
    user_id: str
    available_balance: float
    loan_balance: float
    current_loan_limit: float
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
