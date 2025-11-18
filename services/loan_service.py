import logging
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from db.models.loan import Loan
from db.models.user import User
from db.models.wallet import Wallet
from schemas.loan import LoanCreate, LoanStatus

logger = logging.getLogger(__name__)


class LoanService:
    def __init__(self, db: Session):
        self.db = db

    def check_eligibility(self, user_id: str, requested_amount: float) -> dict:
        """Check if user is eligible for loan"""
        user = self.db.query(User).filter(User.id == user_id).first()
        wallet = self.db.query(Wallet).filter(Wallet.user_id == user_id).first()

        if not user or not wallet:
            return {"eligible": False, "reason": "User not found"}

        # Basic eligibility rules
        if requested_amount > wallet.current_loan_limit:  # type: ignore
            return {"eligible": False, "reason": "Amount exceeds loan limit"}

        if user.credit_score < 300:  # type: ignore
            return {"eligible": False, "reason": "Low credit score"}

        # Check for existing active loans
        active_loans = (
            self.db.query(Loan)
            .filter(
                Loan.user_id == user_id,
                Loan.status.in_(
                    [LoanStatus.PENDING, LoanStatus.APPROVED, LoanStatus.DISBURSED]
                ),
            )
            .count()
        )

        if active_loans > 0:
            return {"eligible": False, "reason": "Existing active loan"}

        return {"eligible": True, "max_amount": wallet.current_loan_limit}

    def create_loan_application(self, loan_data: LoanCreate) -> Loan:
        """Create a new loan application"""
        eligibility = self.check_eligibility(loan_data.user_id, loan_data.amount)
        if not eligibility["eligible"]:
            raise ValueError(eligibility["reason"])

        # Calculate loan details
        interest_amount = loan_data.amount * (15.0 / 100)  # 15% interest
        amount_due = loan_data.amount + interest_amount

        loan = Loan(
            **loan_data.dict(),
            status=LoanStatus.PENDING,
            amount_due=amount_due,
            due_date=datetime.utcnow() + timedelta(days=loan_data.term_days),
        )

        self.db.add(loan)
        self.db.commit()
        self.db.refresh(loan)
        logger.info(f"Created loan application: {loan.id}")
        return loan

    def approve_loan(self, loan_id: str) -> Loan:
        """Approve a loan application"""
        loan = self.db.query(Loan).filter(Loan.id == loan_id).first()
        if loan and loan.status == LoanStatus.PENDING:  # type: ignore
            loan.status = LoanStatus.APPROVED
            loan.approved_date = datetime.utcnow()
            self.db.commit()
            self.db.refresh(loan)
        return loan

    def get_user_loans(self, user_id: str):
        """Get all loans for a user"""
        return (
            self.db.query(Loan)
            .filter(Loan.user_id == user_id)
            .order_by(Loan.application_date.desc())
            .all()
        )
