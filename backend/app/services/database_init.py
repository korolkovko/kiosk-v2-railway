# database_init.py
# Database initialization service for creating default data

from sqlalchemy.orm import Session
from typing import Optional
import logging

from ..database.models import Role, User
from ..auth.password import password_manager

logger = logging.getLogger(__name__)


class DatabaseInitService:
    """Service for initializing database with default data"""
    
    def __init__(self):
        pass
    
    def create_default_roles(self, db: Session) -> None:
        """
        Create default roles if they don't exist
        
        Args:
            db: Database session
        """
        # Define default roles with their permissions
        default_roles = [
            {
                "name": "superadmin",
                "permissions": {
                    "can_create_users": True,
                    "can_manage_users": True,
                    "can_delete_users": True,
                    "can_manage_roles": True,
                    "can_manage_inventory": True,
                    "can_manage_devices": True,
                    "can_manage_settings": True,
                    "can_view_reports": True,
                    "can_manage_branches": True,
                    "full_system_access": True
                }
            },
            {
                "name": "admin", 
                "permissions": {
                    "can_create_users": False,
                    "can_manage_users": False,
                    "can_delete_users": False,
                    "can_manage_roles": False,
                    "can_manage_inventory": True,
                    "can_manage_devices": True,
                    "can_manage_settings": False,
                    "can_view_reports": True,
                    "can_manage_branches": False,
                    "full_system_access": False
                }
            },
            {
                "name": "staff",
                "permissions": {
                    "can_create_users": False,
                    "can_manage_users": False,
                    "can_delete_users": False,
                    "can_manage_roles": False,
                    "can_manage_inventory": False,
                    "can_manage_devices": False,
                    "can_manage_settings": False,
                    "can_view_reports": False,
                    "can_manage_branches": False,
                    "full_system_access": False
                }
            }
        ]
        
        for role_data in default_roles:
            # Check if role already exists
            existing_role = db.query(Role).filter(Role.name == role_data["name"]).first()
            
            if not existing_role:
                # Create new role
                new_role = Role(
                    name=role_data["name"],
                    permissions=role_data["permissions"]
                )
                db.add(new_role)
                logger.info(f"Created default role: {role_data['name']}")
        
        # Commit all role changes
        db.commit()
    
    def has_superadmin(self, db: Session) -> bool:
        """
        Check if any SuperAdmin user exists
        
        Args:
            db: Database session
            
        Returns:
            True if SuperAdmin exists, False otherwise
        """
        superadmin_role = db.query(Role).filter(Role.name == "superadmin").first()
        if not superadmin_role:
            return False
        
        superadmin_user = db.query(User).filter(User.role_name == superadmin_role.name).first()
        return superadmin_user is not None
    
    def create_superadmin(self, db: Session, username: str, password: str, 
                         email: Optional[str] = None, phone: Optional[str] = None) -> User:
        """
        Create a SuperAdmin user
        
        Args:
            db: Database session
            username: SuperAdmin username
            password: SuperAdmin password
            email: Optional email address
            phone: Optional phone number
            
        Returns:
            Created SuperAdmin user
            
        Raises:
            ValueError: If SuperAdmin already exists or role not found
        """
        # Check if SuperAdmin already exists
        if self.has_superadmin(db):
            raise ValueError("SuperAdmin user already exists")
        
        # Get SuperAdmin role
        superadmin_role = db.query(Role).filter(Role.name == "superadmin").first()
        if not superadmin_role:
            raise ValueError("SuperAdmin role not found. Please run database initialization first.")
        
        # Check if username already exists
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            raise ValueError(f"Username '{username}' already exists")
        
        # Hash password
        password_hash = password_manager.hash_password(password)
        
        # Create SuperAdmin user
        superadmin = User(
            username=username,
            password_hash=password_hash,
            email=email,
            phone=phone,
            role_name=superadmin_role.name,
            is_active=True,
            is_verified=True
        )
        
        db.add(superadmin)
        db.commit()
        db.refresh(superadmin)
        
        logger.info(f"Created SuperAdmin user: {username}")
        return superadmin
    
    def create_admin(self, db: Session, username: str, password: str,
                    email: Optional[str] = None, phone: Optional[str] = None) -> User:
        """
        Create an Admin user
        
        Args:
            db: Database session
            username: Admin username
            password: Admin password
            email: Optional email address
            phone: Optional phone number
            
        Returns:
            Created Admin user
            
        Raises:
            ValueError: If username exists or admin role not found
        """
        # Get Admin role
        admin_role = db.query(Role).filter(Role.name == "admin").first()
        if not admin_role:
            raise ValueError("Admin role not found. Please run database initialization first.")
        
        # Check if username already exists
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            raise ValueError(f"Username '{username}' already exists")
        
        # Hash password
        password_hash = password_manager.hash_password(password)
        
        # Create Admin user
        admin = User(
            username=username,
            password_hash=password_hash,
            email=email,
            phone=phone,
            role_name=admin_role.name,
            is_active=True,
            is_verified=True
        )
        
        db.add(admin)
        db.commit()
        db.refresh(admin)
        
        logger.info(f"Created Admin user: {username}")
        return admin
    
    def initialize_database(self, db: Session) -> None:
        """
        Initialize database with default roles and check for SuperAdmin
        
        Args:
            db: Database session
        """
        logger.info("Initializing database with default data...")
        
        # Create default roles
        self.create_default_roles(db)
        
        # Log SuperAdmin status
        if self.has_superadmin(db):
            logger.info("SuperAdmin user already exists")
        else:
            logger.info("No SuperAdmin user found - first-time setup required")
        
        logger.info("Database initialization completed")


# Global database initialization service instance
db_init_service = DatabaseInitService()