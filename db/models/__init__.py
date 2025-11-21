from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

from .loan import Loan
from .transaction import Transaction
from .user import User
from .wallet import Wallet

__all__ = ["Base", "User", "Wallet", "Loan", "Transaction"]
