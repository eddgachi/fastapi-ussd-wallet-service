from typing import Optional
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from core.cache import cache
from core.limiter import limiter
from db.session import get_db
from schemas.loan import LoanResponse, LoanStatus
from services.loan_service import LoanService

router = APIRouter()


@router.get("/loans/user/{user_id}")
@limiter.limit("50/minute")
async def get_user_loans(
    request: Request, user_id: str, db: Session = Depends(get_db)
):
    """
    Get all loans for a user
    """
    cache_key = f"loans:user:{user_id}"
    cached_result = cache.get(cache_key)
    if cached_result:
        return cached_result

    loan_service = LoanService(db)
    loans = loan_service.get_user_loans(user_id)
    
    loans_data = [loan.__dict__ for loan in loans] if loans else []
    for loan in loans_data:
        loan.pop('_sa_instance_state', None)

    cache.set(cache_key, loans_data, expire=60)
    return loans


@router.post("/loans/{loan_id}/approve")
@limiter.limit("5/minute")
async def approve_loan(
    request: Request, loan_id: str, db: Session = Depends(get_db)
):
    """Approve and disburse a loan (triggers Celery workflow)"""
    try:
        loan_service = LoanService(db)
        loan = loan_service.approve_loan(loan_id)
        return {
            "message": "Loan approved and disbursement initiated",
            "loan_details": loan,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/loans/{loan_id}/disburse")
@limiter.limit("5/minute")
async def disburse_loan(
    request: Request,
    loan_id: str,
    mpesa_receipt: str = None,
    db: Session = Depends(get_db),
):
    """Disburse an approved loan"""
    try:
        loan_service = LoanService(db)
        loan = loan_service.disburse_loan(loan_id, mpesa_receipt)

        return {
            "message": "Loan disbursed successfully",
            "loan_id": loan.id,
            "amount": loan.amount,
            "status": loan.status,
            "disbursed_date": (
                loan.disbursed_date.isoformat() if loan.disbursed_date else None
            ),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/notifications/bulk")
async def send_bulk_notifications(
    notifications_data: list, background_tasks: BackgroundTasks
):
    """Send bulk SMS notifications"""
    from core.tasks import process_bulk_sms_notifications

    # Trigger background task
    task = process_bulk_sms_notifications.delay(notifications_data)

    return {"message": "Bulk notifications started", "task_id": task.id}
