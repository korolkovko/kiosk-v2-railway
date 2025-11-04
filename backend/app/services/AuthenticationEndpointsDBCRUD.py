# AuthenticationEndpointsDBCRUD.py
# Database CRUD operations for authentication endpoints
# NOTE: This layer does not perform commit/rollback.
# Transaction management is in the Logic layer.

from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from ..database.models import User


class AuthenticationEndpointsDBCRUD:
    """Database CRUD operations for authentication endpoints"""
    
    def get_user_by_username(self, db: Session, username: str) -> Optional[User]:
        """
        Get user by username
        
        Args:
            db: Database session
            username: Username to search for
            
        Returns:
            User object if found, None otherwise
        """
        return db.query(User).filter(User.username == username).first()
    
    def get_user_by_id(self, db: Session, user_id: int) -> Optional[User]:
        """
        Get user by ID
        
        Args:
            db: Database session
            user_id: User ID to retrieve
            
        Returns:
            User object if found, None otherwise
        """
        return db.query(User).filter(User.user_id == user_id).first()
    
    def update_last_login(self, db: Session, user_id: int) -> None:
        """
        Update user's last login timestamp
        
        Args:
            db: Database session
            user_id: ID of user to update
        """
        db_user = self.get_user_by_id(db, user_id)
        if db_user:
            db_user.last_login_at = datetime.utcnow()
            # Note: No commit here, as per the pattern


# Global service instance
authentication_endpoints_db_crud = AuthenticationEndpointsDBCRUD()