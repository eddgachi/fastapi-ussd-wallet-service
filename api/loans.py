from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from db.session import get_db
from schemas.loan import LoanCreate, LoanResponse
from services.loan_service import LoanService

router = APIRouter()


@router.post("/loans", response_model=LoanResponse)
async def create_loan(loan_data: LoanCreate, db: Session = Depends(get_db)):
    """
    Create a new loan application (for web/admin use)
    """
    try:
        loan_service = LoanService(db)
        loan = loan_service.create_loan_application(loan_data)
        return loan
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/loans/user/{user_id}")
async def get_user_loans(user_id: str, db: Session = Depends(get_db)):
    """
    Get all loans for a user
    """
    loan_service = LoanService(db)
    loans = loan_service.get_user_loans(user_id)
    return loans


@router.post("/loans/{loan_id}/approve")
async def approve_loan(loan_id: str, db: Session = Depends(get_db)):
    """Approve and disburse a loan (triggers Celery workflow)"""
    try:
        loan_service = LoanService(db)
        loan = loan_service.approve_and_disburse_loan(loan_id)
        return {
            "message": "Loan approved and disbursement initiated",
            "loan_id": loan.id,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/loans/repay")
async def repay_loan(
    user_id: str, amount: float, mpesa_receipt: str, db: Session = Depends(get_db)
):
    """Process loan repayment (triggers Celery workflow)"""
    try:
        loan_service = LoanService(db)
        loan_service.process_loan_repayment(user_id, amount, mpesa_receipt)
        return {"message": "Repayment processing initiated"}
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
