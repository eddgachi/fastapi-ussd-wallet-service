import logging

from fastapi import APIRouter, Depends, Request
from fastapi.responses import PlainTextResponse
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from core.limiter import limiter
from db.session import get_db
from services.ussd_service import USSDService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/ussd", response_class=PlainTextResponse)
@limiter.limit("60/minute")
async def handle_ussd(request: Request, db: Session = Depends(get_db)):
    """
    Handle USSD requests from Africa's Talking
    Returns plain text with CON (continue) or END (close session) prefix
    """
    try:
        # Parse form data from Africa's Talking
        form_data = await request.form()

        session_id = form_data.get("sessionId", "")
        service_code = form_data.get("serviceCode", "")
        phone_number = form_data.get("phoneNumber", "")
        text = form_data.get("text", "")

        logger.info(
            f"USSD Request - Session: {session_id}, Phone: {phone_number}, Text: '{text}'"
        )

        # Process USSD request
        ussd_service = USSDService(db)
        message, should_close = ussd_service.process_request(
            session_id=session_id, phone_number=phone_number, text=text
        )

        # Format response for Africa's Talking
        prefix = "END" if should_close else "CON"
        response = f"{prefix} {message}"

        logger.info(f"USSD Response - Session: {session_id}, Close: {should_close}")

        return response

    except Exception as e:
        logger.error(f"USSD endpoint error: {str(e)}", exc_info=True)
        return "END Service temporarily unavailable. Please try again later."


@router.post("/ussd-debug")
async def handle_ussd_debug(request: Request):
    """
    Debug endpoint to inspect Africa's Talking requests
    """
    try:
        # Get the raw request body
        body = await request.body()
        body_str = body.decode("utf-8")

        # Get form data
        form_data = await request.form()

        # Get headers
        headers = dict(request.headers)

        debug_info = {
            "raw_body": body_str,
            "form_data": dict(form_data),
            "headers": headers,
            "method": request.method,
        }

        logger.info(f"USSD Debug: {debug_info}")

        return debug_info

    except Exception as e:
        logger.error(f"Debug endpoint error: {str(e)}")
        return {"error": str(e)}


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "ussd"}
