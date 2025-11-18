from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

from db.models.loan import Loan
from db.models.transaction import Transaction

# Import all models to ensure they are registered with Base
from db.models.user import User
from db.models.wallet import Wallet

__all__ = ["Base", "User", "Loan", "Wallet", "Transaction"]
