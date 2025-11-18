import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, String

from db.session import Base


class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), unique=True, nullable=False)
    available_balance = Column(Float, default=0.0)
    loan_balance = Column(Float, default=0.0)
    total_loan_limit = Column(Float, default=50000.0)  # Maximum loan amount
    current_loan_limit = Column(Float, default=5000.0)  # Current available limit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
