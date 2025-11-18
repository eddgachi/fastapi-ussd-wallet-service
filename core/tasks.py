import time
from datetime import datetime, timedelta

from celery import group, shared_task


@shared_task
def send_sms_notification(phone_number: str, message: str):
    """Background task to send SMS notifications"""
    print(f"Sending SMS to {phone_number}: {message}")
    # Simulate SMS sending (integrate with Africa's Talking or similar)
    time.sleep(2)
    return f"SMS sent to {phone_number}"


@shared_task
def process_mpesa_payment(loan_id: str, amount: float, phone_number: str):
    """Background task to process M-Pesa payments"""
    print(
        f"Processing M-Pesa payment for loan {loan_id}: KES {amount} to {phone_number}"
    )
    # Simulate M-Pesa payment processing
    time.sleep(3)
    return f"Processed payment for loan {loan_id}"


@shared_task
def update_loan_status(loan_id: str, new_status: str):
    """Background task to update loan status"""
    print(f"Updating loan {loan_id} to status: {new_status}")
    # Simulate status update
    time.sleep(1)
    return f"Updated loan {loan_id} to {new_status}"


@shared_task
def calculate_credit_score(user_id: str):
    """Background task to calculate user credit score"""
    print(f"Calculating credit score for user {user_id}")
    # Simulate credit score calculation
    time.sleep(5)
    return f"Credit score calculated for user {user_id}"


@shared_task
def check_due_loans():
    """Check for loans that are due and send reminders"""
    from sqlalchemy import and_

    from db.models.loan import Loan, LoanStatus
    from db.session import get_db

    db = next(get_db())
    try:
        due_date = datetime.utcnow() + timedelta(days=3)  # 3 days from now
        due_loans = (
            db.query(Loan)
            .filter(
                and_(
                    Loan.status == LoanStatus.DISBURSED,
                    Loan.due_date <= due_date,
                    Loan.due_date >= datetime.utcnow(),  # Not overdue yet
                )
            )
            .all()
        )

        for loan in due_loans:
            send_sms_notification.delay(
                loan.user.phone_number,
                f"Reminder: Your loan of KES {loan.amount_due:,.0f} is due on {loan.due_date.strftime('%d/%m/%Y')}. Please repay to avoid penalties.",
            )

        return f"Sent reminders for {len(due_loans)} loans"
    finally:
        db.close()


@shared_task
def check_overdue_loans():
    """Check for overdue loans and update status"""
    from sqlalchemy import and_

    from db.models.loan import Loan, LoanStatus
    from db.session import get_db

    db = next(get_db())
    try:
        overdue_loans = (
            db.query(Loan)
            .filter(
                and_(
                    Loan.status == LoanStatus.DISBURSED,
                    Loan.due_date < datetime.utcnow(),
                )
            )
            .all()
        )

        for loan in overdue_loans:
            loan.status = LoanStatus.DEFAULTED
            send_sms_notification.delay(
                loan.user.phone_number,
                f"URGENT: Your loan is overdue! Amount: KES {loan.amount_due:,.0f}. Please repay immediately.",
            )

        db.commit()
        return f"Updated {len(overdue_loans)} loans to defaulted"
    finally:
        db.close()


@shared_task
def process_bulk_sms_notifications(notifications_data: list):
    """Process multiple SMS notifications in bulk"""
    from core.tasks import send_sms_notification

    # Group the SMS tasks
    job = group(
        send_sms_notification.s(phone, message) for phone, message in notifications_data
    )

    result = job.apply_async()
    return f"Started bulk SMS job: {result.id}"
