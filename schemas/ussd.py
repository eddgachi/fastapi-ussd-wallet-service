from typing import Optional

from pydantic import BaseModel, Field


class USSDRequest(BaseModel):
    """USSD request from Africa's Talking"""

    sessionId: str = Field(..., description="Unique session identifier")
    serviceCode: str = Field(..., description="USSD code dialed")
    phoneNumber: str = Field(..., description="User's phone number")
    text: str = Field(default="", description="User input (* separated)")
    networkCode: Optional[str] = Field(None, description="Mobile network code")

    class Config:
        populate_by_name = True


class USSDResponse(BaseModel):
    """USSD response (for internal use only - not sent to Africa's Talking)"""

    message: str = Field(..., description="Message to display to user")
    should_close: bool = Field(default=False, description="Whether to close session")

    class Config:
        populate_by_name = True
