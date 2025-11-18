import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from db.session import Base


class Loan(Base):
    __tablename__ = "loans"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    term_days = Column(Integer, nullable=False)  # Loan duration in days
    interest_rate = Column(Float, default=15.0)  # 15% interest
    purpose = Column(String(200))
    status = Column(
        String(20), default="pending"
    )  # pending, approved, rejected, disbursed, repaid, defaulted
    application_date = Column(DateTime, default=datetime.utcnow)
    approved_date = Column(DateTime, nullable=True)
    disbursed_date = Column(DateTime, nullable=True)
    due_date = Column(DateTime, nullable=True)
    amount_due = Column(Float, nullable=True)

    # Relationship
    user = relationship("User", backref="loans")
