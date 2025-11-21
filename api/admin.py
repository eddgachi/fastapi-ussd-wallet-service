from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from db.session import get_db
from db.models.user import User
from db.models.loan import Loan
from db.models.wallet import Wallet
from db.models.transaction import Transaction

from schemas.user import UserResponse
from schemas.loan import LoanAdminResponse
from schemas.wallet import WalletResponse
from schemas.transaction import TransactionResponse

from core.cache import cache
from core.limiter import limiter

from schemas.pagination import PaginatedResponse

router = APIRouter()

@router.get("/users", response_model=PaginatedResponse[UserResponse])
@limiter.limit("10/minute")
def get_all_users(request: Request, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all users with pagination metadata"""
    cache_key = f"admin:users:{skip}:{limit}"
    cached_result = cache.get(cache_key)
    if cached_result:
        return cached_result

    total = db.query(User).count()
    users = db.query(User).offset(skip).limit(limit).all()
    
    page = (skip // limit) + 1
    total_pages = (total + limit - 1) // limit

    users_data = [user.__dict__ for user in users]
    for user in users_data:
        user.pop('_sa_instance_state', None)
        
    response_data = {
        "data": users_data,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": total_pages
        }
    }
        
    cache.set(cache_key, response_data, expire=60)
    return response_data

@router.get("/loans", response_model=PaginatedResponse[LoanAdminResponse])
@limiter.limit("10/minute")
def get_all_loans(request: Request, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all loans with pagination metadata"""
    cache_key = f"admin:loans:{skip}:{limit}"
    cached_result = cache.get(cache_key)
    if cached_result:
        return cached_result

    total = db.query(Loan).count()
    loans = db.query(Loan).offset(skip).limit(limit).all()
    
    page = (skip // limit) + 1
    total_pages = (total + limit - 1) // limit
    
    loans_data = [loan.__dict__ for loan in loans]
    for loan in loans_data:
        loan.pop('_sa_instance_state', None)
        
    response_data = {
        "data": loans_data,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": total_pages
        }
    }
        
    cache.set(cache_key, response_data, expire=60)
    return response_data

@router.get("/wallets", response_model=PaginatedResponse[WalletResponse])
@limiter.limit("10/minute")
def get_all_wallets(request: Request, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all wallets with pagination metadata"""
    cache_key = f"admin:wallets:{skip}:{limit}"
    cached_result = cache.get(cache_key)
    if cached_result:
        return cached_result

    total = db.query(Wallet).count()
    wallets = db.query(Wallet).offset(skip).limit(limit).all()
    
    page = (skip // limit) + 1
    total_pages = (total + limit - 1) // limit
    
    wallets_data = [wallet.__dict__ for wallet in wallets]
    for wallet in wallets_data:
        wallet.pop('_sa_instance_state', None)
        
    response_data = {
        "data": wallets_data,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": total_pages
        }
    }
        
    cache.set(cache_key, response_data, expire=60)
    return response_data

@router.get("/transactions", response_model=PaginatedResponse[TransactionResponse])
@limiter.limit("10/minute")
def get_all_transactions(request: Request, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all transactions with pagination metadata"""
    cache_key = f"admin:transactions:{skip}:{limit}"
    cached_result = cache.get(cache_key)
    if cached_result:
        return cached_result

    total = db.query(Transaction).count()
    transactions = db.query(Transaction).offset(skip).limit(limit).all()
    
    page = (skip // limit) + 1
    total_pages = (total + limit - 1) // limit
    
    transactions_data = [txn.__dict__ for txn in transactions]
    for txn in transactions_data:
        txn.pop('_sa_instance_state', None)
        
    response_data = {
        "data": transactions_data,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": total_pages
        }
    }
        
    cache.set(cache_key, response_data, expire=60)
    return response_data
