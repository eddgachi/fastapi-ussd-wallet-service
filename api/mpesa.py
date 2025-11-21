import logging

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from db.session import get_db
from services.mpesa_service import MPESAService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/mpesa/callback")
async def handle_mpesa_callback(request: Request, db: Session = Depends(get_db)):
    """
    Handle M-Pesa STK Push callback

    This endpoint receives payment notifications from Safaricom M-Pesa
    """
    try:
        # Get callback data
        callback_data = await request.json()

        # Log the callback (sanitize sensitive data in production)
        logger.info("Received M-Pesa callback")
        logger.debug(f"Callback data: {callback_data}")

        # Process the callback
        mpesa_service = MPESAService(db)
        result = mpesa_service.handle_callback(callback_data)

        # Return success response to M-Pesa
        if result.get("success"):
            return {"ResultCode": 0, "ResultDesc": "Success"}
        else:
            # Log the error but still return success to M-Pesa
            # to avoid retries for unrecoverable errors
            logger.error(f"Callback processing failed: {result.get('message')}")
            return {"ResultCode": 0, "ResultDesc": "Accepted"}

    except Exception as e:
        logger.error(f"M-Pesa callback error: {str(e)}", exc_info=True)
        # Always return success to M-Pesa to avoid retries
        return {"ResultCode": 0, "ResultDesc": "Accepted"}


@router.post("/mpesa/test-stk")
async def test_stk_push(
    phone_number: str, amount: float, db: Session = Depends(get_db)
):
    """
    Test endpoint for STK Push
    WARNING: Remove or secure this endpoint in production
    """
    try:
        mpesa_service = MPESAService(db)
        result = mpesa_service.initiate_stk_push(
            phone_number=phone_number,
            amount=amount,
            account_reference="TEST123",
            transaction_desc="Test Payment",
        )
        return result
    except Exception as e:
        logger.error(f"Test STK error: {str(e)}")
        return {"success": False, "error": str(e)}


@router.get("/mpesa/query/{checkout_request_id}")
async def query_stk_status(checkout_request_id: str, db: Session = Depends(get_db)):
    """
    Query the status of an STK push transaction
    """
    try:
        mpesa_service = MPESAService(db)
        result = mpesa_service.query_stk_status(checkout_request_id)
        return result
    except Exception as e:
        logger.error(f"Query STK error: {str(e)}")
        return {"success": False, "error": str(e)}


@router.get("/mpesa/health")
async def mpesa_health_check():
    """Health check for M-Pesa integration"""
    return {
        "status": "healthy",
        "service": "mpesa",
        "message": "M-Pesa service is running",
    }
