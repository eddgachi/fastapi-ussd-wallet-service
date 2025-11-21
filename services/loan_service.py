import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from db.models.loan import Loan
from db.models.transaction import Transaction
from db.models.user import User
from db.models.wallet import Wallet
from schemas.loan import LoanStatus

logger = logging.getLogger(__name__)


class LoanService:
    """Improved loan service with better transaction handling"""

    def __init__(self, db: Session):
        self.db = db

    def get_all_loans(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        status: Optional[LoanStatus] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        sort_by: str = "application_date",
        sort_order: str = "desc",
    ):
        """Get all loans with pagination, search, filtering and sorting"""
        query = self.db.query(Loan)

        # Apply filters
        if status:
            query = query.filter(Loan.status == status)

        if min_amount is not None:
            query = query.filter(Loan.amount >= min_amount)

        if max_amount is not None:
            query = query.filter(Loan.amount <= max_amount)

        if search:
            # Search by purpose or user phone number (requires join)
            # For simplicity, let's search by purpose first
            # To search by phone number, we'd need to join with User table
            query = query.join(User).filter(
                (Loan.purpose.ilike(f"%{search}%")) | (User.phone_number.ilike(f"%{search}%"))
            )

        # Apply sorting
        if hasattr(Loan, sort_by):
            column = getattr(Loan, sort_by)
            if sort_order.lower() == "desc":
                query = query.order_by(column.desc())
            else:
                query = query.order_by(column.asc())
        else:
            # Default sort
            query = query.order_by(Loan.application_date.desc())

        return query.offset(skip).limit(limit).all()

    def check_eligibility(self, user_id: str, requested_amount: float) -> dict:
        """Check if user is eligible for loan"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            wallet = self.db.query(Wallet).filter(Wallet.user_id == user_id).first()

            if not user or not wallet:
                return {"eligible": False, "reason": "User not found"}

            # Basic eligibility rules
            if requested_amount <= 0:
                return {"eligible": False, "reason": "Invalid amount"}

            if requested_amount > wallet.current_loan_limit:
                return {
                    "eligible": False,
                    "reason": f"Amount exceeds limit of KES {wallet.current_loan_limit:,.0f}",
                }

            if user.credit_score < 300:
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
                return {"eligible": False, "reason": "You have an active loan"}

            return {"eligible": True, "max_amount": wallet.current_loan_limit}

        except Exception as e:
            logger.error(f"Error checking eligibility: {str(e)}")
            return {"eligible": False, "reason": "System error"}

    def create_loan_application(
        self, user_id: str, amount: float, term_days: int = 30, purpose: str = "General"
    ) -> Optional[Loan]:
        """Create a new loan application with transaction record"""
        try:
            # Check eligibility
            eligibility = self.check_eligibility(user_id, amount)
            if not eligibility["eligible"]:
                raise ValueError(eligibility["reason"])

            # Calculate loan details
            interest_rate = 15.0  # 15% interest
            interest_amount = amount * (interest_rate / 100)
            amount_due = amount + interest_amount
            due_date = datetime.utcnow() + timedelta(days=term_days)

            # Create loan
            loan = Loan(
                user_id=user_id,
                amount=amount,
                term_days=term_days,
                interest_rate=interest_rate,
                purpose=purpose,
                status=LoanStatus.PENDING,
                amount_due=amount_due,
                due_date=due_date,
                application_date=datetime.utcnow(),
            )

            self.db.add(loan)
            self.db.flush()  # Get loan ID without committing

            # Create transaction record
            transaction = Transaction(
                user_id=user_id,
                loan_id=loan.id,
                type="application",
                amount=amount,
                status="pending",
                description=f"Loan application for {purpose}",
            )
            self.db.add(transaction)

            # Commit all changes together
            self.db.commit()
            self.db.refresh(loan)

            logger.info(f"Created loan application: {loan.id} for user {user_id}")
            return loan

        except ValueError as e:
            self.db.rollback()
            logger.warning(f"Loan application denied: {str(e)}")
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating loan: {str(e)}", exc_info=True)
            raise Exception("Unable to process loan application")

    def approve_loan(self, loan_id: str) -> Optional[Loan]:
        """Approve a loan (admin action)"""
        try:
            loan = self.db.query(Loan).filter(Loan.id == loan_id).first()
            if not loan:
                raise ValueError("Loan not found")

            if loan.status != LoanStatus.PENDING:
                raise ValueError(f"Cannot approve loan with status: {loan.status}")

            # Update loan status
            loan.status = LoanStatus.APPROVED
            loan.approved_date = datetime.utcnow()

            # Update transaction
            transaction = (
                self.db.query(Transaction)
                .filter(
                    Transaction.loan_id == loan_id, Transaction.type == "application"
                )
                .first()
            )
            if transaction:
                transaction.status = "approved"

            self.db.commit()
            logger.info(f"Approved loan: {loan_id}")
            return loan

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error approving loan: {str(e)}")
            raise

    def disburse_loan(self, loan_id: str, mpesa_receipt: str = None) -> Optional[Loan]:
        """Disburse approved loan to user"""
        try:
            loan = self.db.query(Loan).filter(Loan.id == loan_id).first()
            if not loan:
                raise ValueError("Loan not found")

            if loan.status != LoanStatus.APPROVED:
                raise ValueError(f"Cannot disburse loan with status: {loan.status}")

            # Get user's wallet
            wallet = (
                self.db.query(Wallet).filter(Wallet.user_id == loan.user_id).first()
            )
            if not wallet:
                raise ValueError("Wallet not found")

            # Update loan status
            loan.status = LoanStatus.DISBURSED
            loan.disbursed_date = datetime.utcnow()

            # Update wallet balances
            wallet.available_balance += loan.amount
            wallet.loan_balance += loan.amount_due
            wallet.current_loan_limit -= loan.amount  # Reduce available limit

            # Create disbursement transaction
            disbursement = Transaction(
                user_id=loan.user_id,
                loan_id=loan.id,
                type="disbursement",
                amount=loan.amount,
                status="completed",
                mpesa_receipt=mpesa_receipt,
                description=f"Loan disbursement - {loan.purpose}",
            )
            self.db.add(disbursement)

            self.db.commit()
            self.db.refresh(loan)

            logger.info(f"Disbursed loan: {loan_id} - Amount: {loan.amount}")
            return loan

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error disbursing loan: {str(e)}")
            raise

    def approve_and_disburse_loan(
        self, loan_id: str, mpesa_receipt: str = None
    ) -> Optional[Loan]:
        """Approve and immediately disburse a loan"""
        try:
            loan = self.db.query(Loan).filter(Loan.id == loan_id).first()
            if not loan:
                raise ValueError("Loan not found")

            if loan.status != "pending":
                raise ValueError(f"Cannot approve loan with status: {loan.status}")

            # Get user's wallet
            wallet = (
                self.db.query(Wallet).filter(Wallet.user_id == loan.user_id).first()
            )
            if not wallet:
                raise ValueError("Wallet not found")

            # Update loan status to approved first
            loan.status = "approved"
            loan.approved_date = datetime.utcnow()

            # Update transaction status
            transaction = (
                self.db.query(Transaction)
                .filter(
                    Transaction.loan_id == loan_id, Transaction.type == "application"
                )
                .first()
            )
            if transaction:
                transaction.status = "approved"

            # Now disburse the loan
            loan.status = "disbursed"
            loan.disbursed_date = datetime.utcnow()

            # Update wallet balances
            wallet.available_balance += loan.amount
            wallet.loan_balance += loan.amount_due
            wallet.current_loan_limit -= loan.amount  # Reduce available limit

            # Create disbursement transaction
            disbursement = Transaction(
                user_id=loan.user_id,
                loan_id=loan.id,
                type="disbursement",
                amount=loan.amount,
                status="completed",
                mpesa_receipt=mpesa_receipt,
                description=f"Loan disbursement - {loan.purpose}",
            )
            self.db.add(disbursement)

            # Send SMS notification (in production, use Celery task)
            try:
                user = self.db.query(User).filter(User.id == loan.user_id).first()
                if user:
                    from core.tasks import send_sms_notification

                    send_sms_notification.delay(
                        user.phone_number,
                        f"Your loan of KES {loan.amount:,.0f} has been approved and disbursed. "
                        f"Ref: {loan.id[:8]}. Check your wallet balance.",
                    )
            except Exception as sms_error:
                logger.warning(f"SMS notification failed: {str(sms_error)}")

            self.db.commit()
            self.db.refresh(loan)

            logger.info(
                f"Approved and disbursed loan: {loan_id} - Amount: {loan.amount}"
            )
            return loan

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error approving and disbursing loan: {str(e)}")
            raise

    def get_active_loan(self, user_id: str) -> Optional[Loan]:
        """Get active loan for user"""
        try:
            return (
                self.db.query(Loan)
                .filter(Loan.user_id == user_id, Loan.status == LoanStatus.DISBURSED)
                .first()
            )
        except Exception as e:
            logger.error(f"Error getting active loan: {str(e)}")
            return None

    def get_user_loans(self, user_id: str, limit: int = 10):
        """Get all loans for a user"""
        try:
            return (
                self.db.query(Loan)
                .filter(Loan.user_id == user_id)
                .order_by(Loan.application_date.desc())
                .limit(limit)
                .all()
            )
        except Exception as e:
            logger.error(f"Error getting user loans: {str(e)}")
            return []

    def record_repayment(
        self, loan_id: str, amount: float, mpesa_receipt: str, phone_number: str
    ) -> dict:
        """Record loan repayment"""
        try:
            loan = self.db.query(Loan).filter(Loan.id == loan_id).first()
            if not loan:
                raise ValueError("Loan not found")

            if loan.status != LoanStatus.DISBURSED:
                raise ValueError(f"Cannot repay loan with status: {loan.status}")

            # Get wallet
            wallet = (
                self.db.query(Wallet).filter(Wallet.user_id == loan.user_id).first()
            )
            if not wallet:
                raise ValueError("Wallet not found")

            # Calculate remaining balance
            remaining = loan.amount_due - amount

            # Create repayment transaction
            repayment = Transaction(
                user_id=loan.user_id,
                loan_id=loan.id,
                type="repayment",
                amount=amount,
                status="completed",
                mpesa_receipt=mpesa_receipt,
                mpesa_phone=phone_number,
                description="Loan repayment via M-Pesa",
            )
            self.db.add(repayment)

            # Update loan status and wallet
            if remaining <= 0:
                # Loan fully repaid
                loan.status = LoanStatus.REPAID
                loan.amount_due = 0
                wallet.loan_balance = 0
                wallet.current_loan_limit += loan.amount  # Restore limit

                # Increase credit score for successful repayment
                user = self.db.query(User).filter(User.id == loan.user_id).first()
                if user:
                    user.credit_score = min(user.credit_score + 50, 850)

                message = f"Loan fully repaid! KES {amount:,.0f} received."
            else:
                # Partial repayment
                loan.amount_due = remaining
                wallet.loan_balance -= amount

                message = f"Payment received: KES {amount:,.0f}. Remaining: KES {remaining:,.0f}"

            self.db.commit()

            logger.info(f"Recorded repayment for loan {loan_id}: {amount}")

            return {
                "success": True,
                "message": message,
                "remaining": remaining,
                "fully_repaid": remaining <= 0,
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error recording repayment: {str(e)}", exc_info=True)
            return {"success": False, "message": str(e)}

    def get_loan_summary(self, user_id: str) -> dict:
        """Get loan summary for user"""
        try:
            wallet = self.db.query(Wallet).filter(Wallet.user_id == user_id).first()
            active_loan = self.get_active_loan(user_id)
            total_loans = self.db.query(Loan).filter(Loan.user_id == user_id).count()

            repaid_loans = (
                self.db.query(Loan)
                .filter(Loan.user_id == user_id, Loan.status == LoanStatus.REPAID)
                .count()
            )

            return {
                "total_loans": total_loans,
                "repaid_loans": repaid_loans,
                "active_loan": active_loan.amount_due if active_loan else 0,
                "available_limit": wallet.current_loan_limit if wallet else 0,
                "loan_balance": wallet.loan_balance if wallet else 0,
            }

        except Exception as e:
            logger.error(f"Error getting loan summary: {str(e)}")
            return {}
