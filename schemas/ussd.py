from pydantic import BaseModel


class USSDRequest(BaseModel):
    session_id: str
    service_code: str
    phone_number: str
    text: str = ""  # USSD input text


class USSDResponse(BaseModel):
    session_id: str
    service_code: str
    message: str
    should_close: bool = False
