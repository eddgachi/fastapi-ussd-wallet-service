import time

from celery import shared_task


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
