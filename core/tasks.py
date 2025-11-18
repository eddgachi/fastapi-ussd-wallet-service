import time

from celery import shared_task

from core.config import settings


@shared_task
def process_harvest_images(harvest_id: str):
    """Background task to process harvest images"""
    print(f"Processing images for harvest {harvest_id}")
    # Simulate image processing
    time.sleep(5)
    return f"Processed images for {harvest_id}"


@shared_task
def generate_qr_code(batch_id: str, batch_code: str):
    """Background task to generate QR code"""
    print(f"Generating QR code for batch {batch_code}")
    # Simulate QR code generation
    time.sleep(2)
    return f"Generated QR code for {batch_code}"


@shared_task
def send_notification(user_id: str, message: str):
    """Background task to send notifications"""
    print(f"Sending notification to user {user_id}: {message}")
    # Simulate notification sending
    time.sleep(1)
    return f"Notification sent to {user_id}"
