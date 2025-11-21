import logging

from sqlalchemy.orm import Session

from db.models.user import User
from db.models.wallet import Wallet
from schemas.user import UserCreate

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_phone(self, phone_number: str) -> User:
        return self.db.query(User).filter(User.phone_number == phone_number).first()

    def create_user(self, user_data: UserCreate) -> User:
        try:
            # Create new user
            user = User(**user_data.dict())
            self.db.add(user)
            self.db.flush()  # Flush to get user ID

            # Create wallet for user
            wallet = Wallet(user_id=user.id)
            self.db.add(wallet)

            self.db.commit()
            self.db.refresh(user)
            logger.info(f"Created new user: {user.phone_number}")
            return user
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating user: {str(e)}")
            raise

    def update_user_credit_score(self, user_id: str, new_score: int) -> User:
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if user:
                user.credit_score = new_score
                self.db.commit()
                self.db.refresh(user)
            return user
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating credit score: {str(e)}")
            raise

    def get_user_wallet(self, user_id: str):
        """Get user's wallet"""
        return self.db.query(Wallet).filter(Wallet.user_id == user_id).first()
