import logging
from typing import Optional

from sqlalchemy.orm import Session

from schemas.ussd import USSDRequest, USSDResponse
from services.loan_service import LoanService
from services.user_service import UserService

logger = logging.getLogger(__name__)


class USSDService:
    def __init__(self, db: Session):
        self.db = db
        self.user_service = UserService(db)
        self.loan_service = LoanService(db)

    def process_ussd_request(self, request: USSDRequest) -> Optional[USSDResponse]:
        phone_number = request.phone_number
        text = request.text.strip()

        # Ensure user exists
        user = self.user_service.get_user_by_phone(phone_number)
        if not user:
            user_data = {"phone_number": phone_number}
            user = self.user_service.create_user(user_data)

        # USSD menu logic
        if text == "":
            # Initial menu
            return USSDResponse(
                session_id=request.session_id,
                service_code=request.service_code,
                message=(
                    "Welcome to Umoja Loans\n"
                    "1. Apply for Loan\n"
                    "2. Check Loan Status\n"
                    "3. Repay Loan\n"
                    "4. Transaction History"
                ),
            )

        # Parse USSD input
        parts = text.split("*")
        current_level = len(parts)

        if parts[0] == "1":  # Loan Application
            return self._handle_loan_application(user, parts, current_level, request)
        elif parts[0] == "2":  # Check Loan Status
            return self._handle_loan_status(user, request)
        elif parts[0] == "3":  # Repay Loan
            return self._handle_loan_repayment(user, request)
        elif parts[0] == "4":  # Transaction History
            return self._handle_transaction_history(user, request)
        else:
            return USSDResponse(
                session_id=request.session_id,
                service_code=request.service_code,
                message="Invalid option. Please try again.",
                should_close=True,
            )

    def _handle_loan_application(self, user, parts, current_level, request):
        if current_level == 1:
            return USSDResponse(
                session_id=request.session_id,
                service_code=request.service_code,
                message="Enter loan amount:",
            )
        elif current_level == 2:
            try:
                amount = float(parts[1])
                return USSDResponse(
                    session_id=request.session_id,
                    service_code=request.service_code,
                    message="Enter loan purpose:\n1. Emergency\n2. Business\n3. Education\n4. Other",
                )
            except ValueError:
                return USSDResponse(
                    session_id=request.session_id,
                    service_code=request.service_code,
                    message="Invalid amount. Please enter a valid number.",
                    should_close=True,
                )
        elif current_level == 3:
            purpose_map = {
                "1": "Emergency",
                "2": "Business",
                "3": "Education",
                "4": "Other",
            }
            purpose = purpose_map.get(parts[2], "General")
            amount = float(parts[1])

            # Create loan application
            try:
                loan_data = {
                    "user_id": user.id,
                    "amount": amount,
                    "term_days": 30,  # Default 30 days
                    "purpose": purpose,
                }
                loan = self.loan_service.create_loan_application(loan_data)

                return USSDResponse(
                    session_id=request.session_id,
                    service_code=request.service_code,
                    message=(
                        f"Loan application received!\n"
                        f"Amount: KES {amount:,.0f}\n"
                        f"Purpose: {purpose}\n"
                        f"Ref: {loan.id[:8]}\n"
                        f"You will receive an SMS confirmation."
                    ),
                    should_close=True,
                )
            except ValueError as e:
                return USSDResponse(
                    session_id=request.session_id,
                    service_code=request.service_code,
                    message=f"Application failed: {str(e)}",
                    should_close=True,
                )

    def _handle_loan_status(self, user, request):
        loans = self.loan_service.get_user_loans(user.id)
        if not loans:
            message = "No loan applications found."
        else:
            latest_loan = loans[0]
            message = (
                f"Latest Loan:\n"
                f"Amount: KES {latest_loan.amount:,.0f}\n"
                f"Status: {latest_loan.status}\n"
                f"Date: {latest_loan.application_date.strftime('%d/%m/%Y')}"
            )

        return USSDResponse(
            session_id=request.session_id,
            service_code=request.service_code,
            message=message,
            should_close=True,
        )

    def _handle_loan_repayment(self, user, request):
        # Simplified repayment menu
        return USSDResponse(
            session_id=request.session_id,
            service_code=request.service_code,
            message=(
                "To repay your loan:\n"
                "1. Go to M-Pesa\n"
                "2. Lipa Na M-Pesa\n"
                "3. Paybill: 123456\n"
                "4. Account: Your Phone\n"
                "We'll confirm via SMS."
            ),
            should_close=True,
        )

    def _handle_transaction_history(self, user, request):
        # Simplified transaction history
        return USSDResponse(
            session_id=request.session_id,
            service_code=request.service_code,
            message=(
                "Transaction History:\n"
                "Visit our website or\n"
                "contact support for\n"
                "detailed history."
            ),
            should_close=True,
        )
