from fastapi import APIRouter, Depends, HTTPException
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
