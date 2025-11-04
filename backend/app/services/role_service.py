# role_service.py
# Service for role management operations

from sqlalchemy.orm import Session
from typing import List, Optional

from ..database.models import Role
from ..models.role import RoleCreate, RoleUpdate


class RoleService:
    """Service for role management operations"""
    
    def __init__(self):
        pass
    
    def get_role_by_id(self, db: Session, role_id: int) -> Optional[Role]:
        """
        Get role by ID
        
        Args:
            db: Database session
            role_id: Role ID to retrieve
            
        Returns:
            Role object if found, None otherwise
        """
        return db.query(Role).filter(Role.role_id == role_id).first()
    
    def get_role_by_name(self, db: Session, name: str) -> Optional[Role]:
        """
        Get role by name
        
        Args:
            db: Database session
            name: Role name to search for
            
        Returns:
            Role object if found, None otherwise
        """
        return db.query(Role).filter(Role.name == name).first()
    
    def get_roles(self, db: Session, skip: int = 0, limit: int = 100) -> List[Role]:
        """
        Get list of roles with pagination
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of Role objects
        """
        return db.query(Role).offset(skip).limit(limit).all()
    
    def create_role(self, db: Session, role_create: RoleCreate) -> Role:
        """
        Create a new role
        
        Args:
            db: Database session
            role_create: Role creation data
            
        Returns:
            Created Role object
            
        Raises:
            ValueError: If role name already exists
        """
        # Check if role name already exists
        if self.get_role_by_name(db, role_create.name):
            raise ValueError(f"Role '{role_create.name}' already exists")
        
        # Create role object
        db_role = Role(
            name=role_create.name,
            permissions=role_create.permissions
        )
        
        # Save to database
        db.add(db_role)
        db.commit()
        db.refresh(db_role)
        
        return db_role
    
    def update_role(self, db: Session, role_id: int, role_update: RoleUpdate) -> Optional[Role]:
        """
        Update an existing role
        
        Args:
            db: Database session
            role_id: ID of role to update
            role_update: Role update data
            
        Returns:
            Updated Role object if found, None otherwise
            
        Raises:
            ValueError: If role name already exists for another role
        """
        # Get existing role
        db_role = self.get_role_by_id(db, role_id)
        if not db_role:
            return None
        
        # Check name uniqueness (if being updated)
        if role_update.name and role_update.name != db_role.name:
            existing_role = self.get_role_by_name(db, role_update.name)
            if existing_role and existing_role.role_id != role_id:
                raise ValueError(f"Role name '{role_update.name}' already exists")
        
        # Update fields
        update_data = role_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_role, field, value)
        
        # Save changes
        db.commit()
        db.refresh(db_role)
        
        return db_role
    
    def delete_role(self, db: Session, role_id: int) -> bool:
        """
        Delete a role
        
        Args:
            db: Database session
            role_id: ID of role to delete
            
        Returns:
            True if role was deleted, False if role not found
        """
        db_role = self.get_role_by_id(db, role_id)
        if not db_role:
            return False
        
        db.delete(db_role)
        db.commit()
        
        return True


# Global role service instance
role_service = RoleService()