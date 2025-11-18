import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, String, Text

from db.session import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    loan_id = Column(String, ForeignKey("loans.id"), nullable=True)
    type = Column(String(20), nullable=False)  # disbursement, repayment, fee
    amount = Column(Float, nullable=False)
    mpesa_receipt = Column(String(50), nullable=True)
    mpesa_phone = Column(String(15), nullable=True)
    status = Column(String(20), default="pending")  # pending, completed, failed
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
