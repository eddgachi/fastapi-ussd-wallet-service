import logging
from datetime import datetime, timedelta

from celery import chain, group
from sqlalchemy.orm import Session

from core.tasks import (
    calculate_credit_score,
    process_mpesa_payment,
    send_sms_notification,
    update_loan_status,
)
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

    def approve_and_disburse_loan(self, loan_id: str) -> Loan:
        """Approve loan and initiate disbursement process"""
        loan = self.db.query(Loan).filter(Loan.id == loan_id).first()
        if not loan:
            raise ValueError("Loan not found")

        # Update loan status to approved
        loan.status = LoanStatus.APPROVED
        loan.approved_date = datetime.utcnow()
        self.db.commit()

        # Start the disbursement workflow
        self._initiate_loan_disbursement_workflow(loan)

        return loan

    def _initiate_loan_disbursement_workflow(self, loan: Loan):
        """Start the Celery workflow for loan disbursement"""
        try:
            # Chain tasks: Update status → Process payment → Send notification → Calculate credit
            workflow = chain(
                update_loan_status.s(loan.id, "processing_disbursement"),
                process_mpesa_payment.s(loan.amount, loan.user.phone_number),
                update_loan_status.s("disbursed"),
                send_sms_notification.s(
                    loan.user.phone_number,
                    f"Your loan of KES {loan.amount:,.0f} has been disbursed to your M-Pesa.",
                ),
                calculate_credit_score.s(loan.user_id),
            )

            # Execute the workflow
            workflow.apply_async()
            logger.info(f"Started disbursement workflow for loan {loan.id}")

        except Exception as e:
            logger.error(f"Failed to start disbursement workflow: {str(e)}")
            # Fallback: update status to failed
            update_loan_status.delay(loan.id, "disbursement_failed")

    def process_loan_repayment(self, user_id: str, amount: float, mpesa_receipt: str):
        """Process loan repayment from user"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")

        # Find active loan for user
        active_loan = (
            self.db.query(Loan)
            .filter(Loan.user_id == user_id, Loan.status == LoanStatus.DISBURSED)
            .first()
        )

        if not active_loan:
            raise ValueError("No active loan found")

        # Start repayment workflow
        self._initiate_repayment_workflow(active_loan, amount, mpesa_receipt)

    def _initiate_repayment_workflow(
        self, loan: Loan, amount: float, mpesa_receipt: str
    ):
        """Start Celery workflow for loan repayment"""
        try:
            # Group tasks that can run in parallel
            parallel_tasks = group(
                update_loan_status.s(loan.id, "repayment_received"),
                send_sms_notification.s(
                    loan.user.phone_number,
                    f"Payment of KES {amount:,.0f} received. Receipt: {mpesa_receipt}",
                ),
            )

            # Chain: parallel tasks → credit score update
            workflow = chain(parallel_tasks, calculate_credit_score.s(loan.user_id))

            workflow.apply_async()
            logger.info(f"Started repayment workflow for loan {loan.id}")

        except Exception as e:
            logger.error(f"Failed to start repayment workflow: {str(e)}")
