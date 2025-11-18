from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.session import get_db
from schemas.ussd import USSDRequest, USSDResponse
from services.ussd_service import USSDService

router = APIRouter()


@router.post("/ussd", response_model=USSDResponse)
async def handle_ussd(request: USSDRequest, db: Session = Depends(get_db)):
    """
    Handle USSD requests from telecom providers
    """
    try:
        ussd_service = USSDService(db)
        response = ussd_service.process_ussd_request(request)
        return response
    except Exception as e:
        # Log the error but return user-friendly message
        return USSDResponse(
            session_id=request.session_id,
            service_code=request.service_code,
            message="Service temporarily unavailable. Please try again later.",
            should_close=True,
        )
