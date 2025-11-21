import logging
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from db.models.user import User
from db.models.wallet import Wallet
from schemas.loan import LoanStatus
from services.loan_service import LoanService
from services.mpesa_service import MPESAService

logger = logging.getLogger(__name__)


class USSDService:
    """
    Improved USSD Service with better error handling and M-Pesa integration
    """

    def __init__(self, db: Session):
        self.db = db
        self.loan_service = LoanService(db)
        self.mpesa_service = MPESAService(db)

    def process_request(
        self, session_id: str, phone_number: str, text: str
    ) -> Tuple[str, bool]:
        """
        Process USSD request and return (message, should_close)
        """
        try:
            # Ensure user exists
            user = self._get_or_create_user(phone_number)
            if not user:
                return "Service error. Please try again later.", True

            # Parse user input
            text = text.strip()

            # Main menu (empty text = new session)
            if text == "":
                return self._show_main_menu(), False

            # Split input by * to get menu path
            inputs = text.split("*")
            menu_choice = inputs[0]

            # Route to appropriate handler
            if menu_choice == "1":
                return self._handle_loan_application(user, inputs)
            elif menu_choice == "2":
                return self._handle_loan_status(user, inputs)
            elif menu_choice == "3":
                return self._handle_loan_repayment(user, inputs)
            elif menu_choice == "4":
                return self._handle_transaction_history(user, inputs)
            elif menu_choice == "5":
                return self._handle_wallet_balance(user, inputs)
            else:
                return "Invalid option. Please try again.", True

        except Exception as e:
            logger.error(f"USSD processing error: {str(e)}", exc_info=True)
            return "Service temporarily unavailable. Please try again.", True

    def _get_or_create_user(self, phone_number: str) -> Optional[User]:
        """Get existing user or create new one"""
        try:
            user = self.db.query(User).filter(User.phone_number == phone_number).first()

            if not user:
                logger.info(f"Creating new user: {phone_number}")
                user = User(phone_number=phone_number)
                self.db.add(user)
                self.db.flush()

                # Create wallet for new user
                wallet = Wallet(user_id=user.id)
                self.db.add(wallet)

                self.db.commit()
                self.db.refresh(user)
                logger.info(f"Created user {user.id} with wallet")

            return user
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error getting/creating user: {str(e)}")
            return None

    def _show_main_menu(self) -> str:
        """Display main menu"""
        return (
            "Welcome to Umoja Loans\n"
            "1. Apply for Loan\n"
            "2. Check Loan Status\n"
            "3. Repay Loan\n"
            "4. Transaction History\n"
            "5. Wallet Balance"
        )

    def _handle_loan_application(self, user: User, inputs: list) -> Tuple[str, bool]:
        """
        Handle loan application flow
        Flow: Main menu > Enter amount > Select purpose > Confirmation
        """
        level = len(inputs)

        try:
            if level == 1:
                # Step 1: Show available limit and ask for amount
                wallet = self.db.query(Wallet).filter(Wallet.user_id == user.id).first()
                if not wallet:
                    return "Wallet not found. Contact support.", True

                return (
                    f"Apply for Loan\n"
                    f"Available: KES {wallet.current_loan_limit:,.0f}\n"
                    f"Enter amount:"
                ), False

            elif level == 2:
                # Step 2: Validate amount and ask for purpose
                try:
                    amount = float(inputs[1])

                    if amount <= 0:
                        return (
                            "Amount must be greater than 0.\nEnter valid amount:",
                            False,
                        )

                    # Check eligibility
                    eligibility = self.loan_service.check_eligibility(user.id, amount)
                    if not eligibility["eligible"]:
                        return f"Sorry: {eligibility['reason']}", True

                    return (
                        f"Amount: KES {amount:,.0f}\n"
                        f"Select purpose:\n"
                        f"1. Emergency\n"
                        f"2. Business\n"
                        f"3. Education\n"
                        f"4. Personal"
                    ), False

                except ValueError:
                    return "Invalid amount.\nEnter numbers only:", False

            elif level == 3:
                # Step 3: Create loan application
                try:
                    amount = float(inputs[1])
                    purpose_choice = inputs[2]

                    purpose_map = {
                        "1": "Emergency",
                        "2": "Business",
                        "3": "Education",
                        "4": "Personal",
                    }
                    purpose = purpose_map.get(purpose_choice, "General")

                    # Create loan application with correct parameters
                    loan = self.loan_service.create_loan_application(
                        user_id=user.id, amount=amount, term_days=30, purpose=purpose
                    )

                    # Check if loan was created successfully
                    if not loan:
                        return "Application failed. Please try again.", True

                    # Calculate total due for display
                    total_due = loan.amount_due if loan.amount_due else (amount * 1.15)

                    # Queue SMS notification without blocking
                    try:
                        from core.tasks import send_sms_notification

                        send_sms_notification.delay(
                            user.phone_number,
                            f"Loan application received for KES {amount:,.0f}. "
                            f"Ref: {loan.id[:8]}. We'll notify you once approved.",
                        )
                    except Exception as sms_error:
                        # Don't fail the whole request if SMS fails
                        logger.error(f"SMS notification failed: {str(sms_error)}")

                    return (
                        f"Application Submitted!\n"
                        f"Amount: KES {amount:,.0f}\n"
                        f"Purpose: {purpose}\n"
                        f"Interest: 15%\n"
                        f"Total Due: KES {total_due:,.0f}\n"
                        f"Due: {loan.due_date.strftime('%d/%m/%Y') if loan.due_date else 'TBD'}\n"
                        f"Ref: {loan.id[:8]}\n"
                        f"You'll receive SMS confirmation."
                    ), True

                except ValueError as e:
                    return f"Application failed: {str(e)}", True
                except Exception as e:
                    logger.error(f"Loan application error: {str(e)}", exc_info=True)
                    return "Application failed. Please try again.", True

            else:
                return "Invalid input.", True

        except Exception as e:
            logger.error(f"Loan application error: {str(e)}", exc_info=True)
            return "Error processing application.", True

    def _handle_loan_status(self, user: User, inputs: list) -> Tuple[str, bool]:
        """Check loan status"""
        try:
            loans = self.loan_service.get_user_loans(user.id, limit=1)

            if not loans:
                return "No loan applications found.", True

            # Show latest loan
            latest = loans[0]

            # Fix: Handle status properly - it's stored as string, not enum
            status_display = latest.status.upper() if latest.status else "UNKNOWN"

            # Map status to more user-friendly display
            status_map = {
                "pending": "PENDING REVIEW",
                "approved": "APPROVED",
                "rejected": "REJECTED",
                "disbursed": "ACTIVE",
                "repaid": "REPAID",
                "defaulted": "DEFAULTED",
            }
            status_display = status_map.get(latest.status.lower(), status_display)

            message = (
                f"Latest Loan\n"
                f"Amount: KES {latest.amount:,.0f}\n"
                f"Status: {status_display}\n"
                f"Purpose: {latest.purpose}\n"
                f"Applied: {latest.application_date.strftime('%d/%m/%Y')}"
            )

            # Add due information for active loans
            if latest.status.lower() == "disbursed" and latest.amount_due:
                message += (
                    f"\n\nAmount Due: KES {latest.amount_due:,.0f}\n"
                    f"Due Date: {latest.due_date.strftime('%d/%m/%Y') if latest.due_date else 'TBD'}"
                )
            elif latest.status.lower() == "repaid":
                message += "\n\nLoan fully repaid!"
            elif latest.status.lower() == "approved":
                message += "\n\nLoan approved! Awaiting disbursement."

            return message, True

        except Exception as e:
            logger.error(f"Loan status error: {str(e)}", exc_info=True)
            return "Error checking status.", True

    def _handle_loan_repayment(self, user: User, inputs: list) -> Tuple[str, bool]:
        """Handle loan repayment with M-Pesa STK Push"""
        level = len(inputs)

        try:
            if level == 1:
                # Step 1: Check for active loan
                active_loan = self.loan_service.get_active_loan(user.id)

                if not active_loan:
                    return "No active loan to repay.", True

                return (
                    f"Loan Repayment\n"
                    f"Loan: KES {active_loan.amount:,.0f}\n"
                    f"Due: KES {active_loan.amount_due:,.0f}\n"
                    f"Due Date: {active_loan.due_date.strftime('%d/%m/%Y')}\n"
                    f"\nEnter amount to pay:"
                ), False

            elif level == 2:
                # Step 2: Initiate M-Pesa STK Push
                try:
                    amount = float(inputs[1])

                    if amount <= 0:
                        return "Amount must be greater than 0.", True

                    if amount < 10:
                        return "Minimum payment is KES 10.", True

                    # Get active loan
                    active_loan = self.loan_service.get_active_loan(user.id)

                    if not active_loan:
                        return "No active loan found.", True

                    if amount > active_loan.amount_due:
                        return (
                            f"Amount exceeds due.\n"
                            f"Maximum: KES {active_loan.amount_due:,.0f}"
                        ), True

                    # Initiate STK Push with improved error handling
                    stk_result = self.mpesa_service.initiate_stk_push(
                        phone_number=user.phone_number,
                        amount=amount,
                        account_reference=f"{active_loan.id[:8]}",
                        transaction_desc="Loan Payment",
                    )

                    if stk_result["success"]:
                        checkout_id = stk_result.get("checkout_request_id", "")
                        return (
                            f"Payment Request Sent!\n"
                            f"Amount: KES {amount:,.0f}\n"
                            f"Check your phone to complete.\n"
                            f"Enter M-Pesa PIN to confirm."
                        ), True
                    else:
                        error_msg = stk_result.get("message", "Payment failed")
                        return f"Payment Failed:\n{error_msg}", True

                except ValueError:
                    return "Invalid amount.\nEnter numbers only.", True

            else:
                return "Invalid input.", True

        except Exception as e:
            logger.error(f"Repayment error: {str(e)}", exc_info=True)
            return "Error processing payment.", True

    def _handle_transaction_history(self, user: User, inputs: list) -> Tuple[str, bool]:
        """Show transaction history"""
        try:
            from db.models.transaction import Transaction

            transactions = (
                self.db.query(Transaction)
                .filter(Transaction.user_id == user.id)
                .order_by(Transaction.created_at.desc())
                .limit(3)
                .all()
            )

            if not transactions:
                return "No transactions found.", True

            message = "Recent Transactions\n"
            for i, txn in enumerate(transactions, 1):
                txn_type = txn.type.capitalize()
                date_str = txn.created_at.strftime("%d/%m/%Y")

                message += f"\n{i}. {txn_type}\n"
                message += f"   KES {txn.amount:,.0f}\n"
                message += f"   {date_str}\n"
                message += f"   {txn.status.upper()}"

                if txn.mpesa_receipt:
                    message += f"\n   Ref: {txn.mpesa_receipt[:10]}"

            return message, True

        except Exception as e:
            logger.error(f"Transaction history error: {str(e)}")
            return "No history available.", True

    def _handle_wallet_balance(self, user: User, inputs: list) -> Tuple[str, bool]:
        """Show wallet balance and loan summary"""
        try:
            wallet = self.db.query(Wallet).filter(Wallet.user_id == user.id).first()

            if not wallet:
                return "Wallet not found.", True

            # Get loan summary
            summary = self.loan_service.get_loan_summary(user.id)

            message = (
                f"Your Wallet\n"
                f"Balance: KES {wallet.available_balance:,.0f}\n"
                f"Loan Balance: KES {wallet.loan_balance:,.0f}\n"
                f"Loan Limit: KES {wallet.current_loan_limit:,.0f}\n"
                f"Credit Score: {user.credit_score}\n"
                f"\nTotal Loans: {summary.get('total_loans', 0)}\n"
                f"Repaid: {summary.get('repaid_loans', 0)}"
            )

            return message, True

        except Exception as e:
            logger.error(f"Wallet balance error: {str(e)}")
            return "Error checking balance.", True
