# SuperAdminInitDBCRUD.py
# Database CRUD operations for SuperAdmin initialization
# NOTE: This layer does not perform commit/rollback.
# Transaction management is in the Logic layer.

from sqlalchemy.orm import Session
from typing import Optional

from ..database.models import User, Role
from ..models.SuperAdminInitPydanticModel import SuperAdminSetupRequest


class SuperAdminInitDBCRUD:
    """Database CRUD operations for SuperAdmin initialization"""
    
    def get_superadmin_role(self, db: Session) -> Optional[Role]:
        """
        Get SuperAdmin role
        
        Args:
            db: Database session
            
        Returns:
            SuperAdmin Role object if found, None otherwise
        """
        return db.query(Role).filter(Role.name == "superadmin").first()
    
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
    
    def has_superadmin(self, db: Session) -> bool:
        """
        Check if any SuperAdmin user exists
        
        Args:
            db: Database session
            
        Returns:
            True if SuperAdmin exists, False otherwise
        """
        superadmin_role = self.get_superadmin_role(db)
        if not superadmin_role:
            return False
        
        superadmin_user = db.query(User).filter(User.role_name == superadmin_role.name).first()
        return superadmin_user is not None
    
    def create_superadmin(self, db: Session, setup_request: SuperAdminSetupRequest, 
                          password_hash: str, role_name: str) -> User:
        """
        Create a SuperAdmin user
        
        Args:
            db: Database session
            setup_request: SuperAdmin setup request data
            password_hash: Hashed password
            role_name: SuperAdmin role name
            
        Returns:
            Created SuperAdmin user
        """
        # Create SuperAdmin user
        superadmin = User(
            username=setup_request.username,
            password_hash=password_hash,
            email=setup_request.email,
            phone=setup_request.phone,
            role_name=role_name,
            is_active=True,
            is_verified=True
        )
        
        # Add to database (no commit)
        db.add(superadmin)
        db.flush()
        
        return superadmin


# Global service instance
superadmin_init_db_crud = SuperAdminInitDBCRUD()