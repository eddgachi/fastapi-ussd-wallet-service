import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Index, String, Text
from sqlalchemy.orm import relationship

from db.models import Base


class Transaction(Base):
    """
    Improved transaction model with better tracking and indexing
    """

    __tablename__ = "transactions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    loan_id = Column(String, ForeignKey("loans.id"), nullable=True, index=True)

    # Transaction details
    type = Column(
        String(20), nullable=False, index=True
    )  # application, disbursement, repayment, fee

    amount = Column(Float, nullable=False)

    # M-Pesa specific fields
    mpesa_receipt = Column(String(50), nullable=True, unique=True, index=True)
    mpesa_phone = Column(String(15), nullable=True)
    checkout_request_id = Column(String(100), nullable=True, index=True)

    # Status tracking
    status = Column(
        String(20), default="pending", index=True
    )  # pending, completed, failed, cancelled

    # Additional details
    description = Column(Text)
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", backref="transactions")
    loan = relationship("Loan", backref="transactions")

    # Composite indexes for common queries
    __table_args__ = (
        Index("idx_user_type_status", "user_id", "type", "status"),
        Index("idx_loan_type", "loan_id", "type"),
        Index("idx_created_status", "created_at", "status"),
    )

    def __repr__(self):
        return f"<Transaction(id={self.id[:8]}, type={self.type}, amount={self.amount}, status={self.status})>"

    def to_dict(self):
        """Convert transaction to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "loan_id": self.loan_id,
            "type": self.type,
            "amount": self.amount,
            "mpesa_receipt": self.mpesa_receipt,
            "mpesa_phone": self.mpesa_phone,
            "status": self.status,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
        }
