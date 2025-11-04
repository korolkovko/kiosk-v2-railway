# UserManagementDBCRUD.py
# Database CRUD operations for user management endpoints
# NOTE: This layer does not perform commit/rollback.
# Transaction management is in the Logic layer.

from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from ..database.models import User, Role
from ..models.UserManagementPydanticModel import UserCreate, UserUpdate
from ..auth.password import password_manager


class UserManagementDBCRUD:
    """Database CRUD operations for user management"""
    
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
    
    def create_user(self, db: Session, user_create: UserCreate, password_hash: str) -> User:
        """
        Create a new user
        
        Args:
            db: Database session
            user_create: User creation data
            password_hash: Hashed password
            
        Returns:
            Created User object
        """
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
        
        # Add to database (no commit)
        db.add(db_user)
        db.flush()
        
        return db_user
    
    def create_admin_user(self, db: Session, admin_data, admin_role_name: str, password_hash: str) -> User:
        """
        Create a new admin user
        
        Args:
            db: Database session
            admin_data: Admin user creation data
            admin_role_name: Admin role name
            password_hash: Hashed password
            
        Returns:
            Created admin User object
        """
        # Create admin user with admin role_name
        admin_user = User(
            username=admin_data.username,
            password_hash=password_hash,
            email=admin_data.email,
            phone=admin_data.phone,
            role_name=admin_role_name,
            is_active=admin_data.is_active,
            is_verified=admin_data.is_verified
        )
        
        # Add to database (no commit)
        db.add(admin_user)
        db.flush()
        
        return admin_user
    
    def update_user(self, db: Session, db_user: User, user_update: UserUpdate) -> User:
        """
        Update an existing user
        
        Args:
            db: Database session
            db_user: Existing user object to update
            user_update: User update data
            
        Returns:
            Updated User object
        """
        # Update fields
        update_data = user_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_user, field, value)
        
        # Set updated timestamp
        db_user.updated_at = datetime.utcnow()
        
        # Flush changes (no commit)
        db.flush()
        
        return db_user
    
    def delete_user(self, db: Session, db_user: User) -> None:
        """
        Delete a user
        
        Args:
            db: Database session
            db_user: User object to delete
        """
        db.delete(db_user)
        # No commit here, as per the pattern
    
    def get_role_by_name(self, db: Session, role_name: str) -> Optional[Role]:
        """
        Get role by name
        
        Args:
            db: Database session
            role_name: Role name to search for
            
        Returns:
            Role object if found, None otherwise
        """
        return db.query(Role).filter(Role.name == role_name).first()


# Global service instance
user_management_db_crud = UserManagementDBCRUD()