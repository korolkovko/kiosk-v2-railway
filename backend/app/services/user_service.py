# user_service.py
# Service for user management operations

from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from ..database.models import User, Role
from ..models.user import UserCreate, UserUpdate
from ..auth.password import password_manager


class UserService:
    """Service for user management operations"""
    
    def __init__(self):
        pass
    
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
    
    def get_user_by_email(self, db: Session, email: str) -> Optional[User]:
        """
        Get user by email
        
        Args:
            db: Database session
            email: Email to search for
            
        Returns:
            User object if found, None otherwise
        """
        return db.query(User).filter(User.email == email).first()
    
    def get_users(self, db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Get list of users with pagination
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of User objects
        """
        return db.query(User).offset(skip).limit(limit).all()
    
    def create_user(self, db: Session, user_create: UserCreate) -> User:
        """
        Create a new user
        
        Args:
            db: Database session
            user_create: User creation data
            
        Returns:
            Created User object
            
        Raises:
            ValueError: If username or email already exists, or role not found
        """
        # Check if username already exists
        if self.get_user_by_username(db, user_create.username):
            raise ValueError(f"Username '{user_create.username}' already exists")
        
        # Check if email already exists (if provided)
        if user_create.email and self.get_user_by_email(db, user_create.email):
            raise ValueError(f"Email '{user_create.email}' already exists")
        
        # Verify role exists
        role = db.query(Role).filter(Role.name == user_create.role_name).first()
        if not role:
            raise ValueError(f"Role with name '{user_create.role_name}' not found")
        
        # Hash password
        password_hash = password_manager.hash_password(user_create.password)
        
        # Create user object
        db_user = User(
            username=user_create.username,
            password_hash=password_hash,
            email=user_create.email,
            phone=user_create.phone,
            role_name=user_create.role_name,
            is_active=user_create.is_active,
            is_verified=user_create.is_verified
        )
        
        # Save to database
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        return db_user
    
    def update_user(self, db: Session, user_id: int, user_update: UserUpdate) -> Optional[User]:
        """
        Update an existing user
        
        Args:
            db: Database session
            user_id: ID of user to update
            user_update: User update data
            
        Returns:
            Updated User object if found, None otherwise
            
        Raises:
            ValueError: If username or email already exists for another user
        """
        # Get existing user
        db_user = self.get_user_by_id(db, user_id)
        if not db_user:
            return None
        
        # Check username uniqueness (if being updated)
        if user_update.username and user_update.username != db_user.username:
            existing_user = self.get_user_by_username(db, user_update.username)
            if existing_user and existing_user.user_id != user_id:
                raise ValueError(f"Username '{user_update.username}' already exists")
        
        # Check email uniqueness (if being updated)
        if user_update.email and user_update.email != db_user.email:
            existing_user = self.get_user_by_email(db, user_update.email)
            if existing_user and existing_user.user_id != user_id:
                raise ValueError(f"Email '{user_update.email}' already exists")
        
        # Verify role exists (if being updated)
        if user_update.role_name and user_update.role_name != db_user.role_name:
            role = db.query(Role).filter(Role.name == user_update.role_name).first()
            if not role:
                raise ValueError(f"Role with name '{user_update.role_name}' not found")
        
        # Update fields
        update_data = user_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_user, field, value)
        
        # Set updated timestamp
        db_user.updated_at = datetime.utcnow()
        
        # Save changes
        db.commit()
        db.refresh(db_user)
        
        return db_user
    
    def delete_user(self, db: Session, user_id: int) -> bool:
        """
        Delete a user
        
        Args:
            db: Database session
            user_id: ID of user to delete
            
        Returns:
            True if user was deleted, False if user not found
        """
        db_user = self.get_user_by_id(db, user_id)
        if not db_user:
            return False
        
        db.delete(db_user)
        db.commit()
        
        return True
    
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
            db.commit()


# Global user service instance
user_service = UserService()