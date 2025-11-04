# UserManagementLogic.py
# Business logic for user management endpoints
# NOTE: This layer manages full transaction: validation → operation → commit/rollback

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional

from ..models.UserManagementPydanticModel import UserCreate, UserUpdate, UserResponse, AdminCreate
from ..services.UserManagementDBCRUD import user_management_db_crud
from ..database.models import User, KioskServiceMode
from ..auth.password import password_manager


class UserManagementLogic:
    """Business logic for user management endpoints"""
    
    async def create_admin_user(self, db: Session, user_data: AdminCreate, current_user: User) -> User:
        """
        Create a new Admin user
        
        Args:
            db: Database session
            user_data: Admin user creation data
            current_user: Current SuperAdmin user
            
        Returns:
            Created admin user
            
        Raises:
            HTTPException: If admin role not found or user creation fails
        """
        try:
            # Check if 'admin' role exists
            admin_role = user_management_db_crud.get_role_by_name(db, "admin")
            if not admin_role:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No such role 'admin' found in roles table"
                )
            
            # Check if username already exists
            existing_user = user_management_db_crud.get_user_by_username(db, user_data.username)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Username '{user_data.username}' already exists"
                )
            
            # Hash password
            password_hash = password_manager.hash_password(user_data.password)
            
            # Create admin user with admin role_name
            admin_user = user_management_db_crud.create_admin_user(
                db=db,
                admin_data=user_data,
                admin_role_name=admin_role.name,
                password_hash=password_hash
            )
            
            # Commit transaction
            db.commit()
            db.refresh(admin_user)
            
            return admin_user
            
        except HTTPException:
            db.rollback()
            raise
        except ValueError as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create admin user: {str(e)}"
            )
    
    async def create_kiosk_user(self, db: Session, user_data, current_user: User) -> User:
        """
        Create a new Kiosk user

        Args:
            db: Database session
            user_data: Kiosk user creation data
            current_user: Current SuperAdmin user

        Returns:
            Created kiosk user

        Raises:
            HTTPException: If kiosk role not found or user creation fails
        """
        try:
            # Check if 'kiosk' role exists
            kiosk_role = user_management_db_crud.get_role_by_name(db, "kiosk")
            if not kiosk_role:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No such role 'kiosk' found in roles table"
                )

            # Check if username already exists
            existing_user = user_management_db_crud.get_user_by_username(db, user_data.username)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Username '{user_data.username}' already exists"
                )

            # Hash password
            password_hash = password_manager.hash_password(user_data.password)

            # Create kiosk user with kiosk role_name (email and phone are optional)
            kiosk_user = User(
                username=user_data.username,
                password_hash=password_hash,
                email=None,  # Kiosk users don't need email
                phone=None,  # Kiosk users don't need phone
                role_name=kiosk_role.name,
                is_active=user_data.is_active,
                is_verified=user_data.is_verified
            )
            
            db.add(kiosk_user)
            db.flush()  # Flush to get the ID
            
            # Create corresponding service mode entry for the kiosk user
            kiosk_service_mode = KioskServiceMode(
                kiosk_username=kiosk_user.username,
                is_service_mode=False,  # Default to not in service mode
                service_picture_name=None  # No picture initially
            )
            
            db.add(kiosk_service_mode)
            db.flush()  # Flush to ensure both records are created

            db.commit()
            db.refresh(kiosk_user)

            return kiosk_user

        except HTTPException:
            db.rollback()
            raise
        except ValueError as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create kiosk user: {str(e)}"
            )
    async def get_users(self, db: Session, skip: int, limit: int, current_user: User) -> List[User]:
        """
        Get list of all users
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            current_user: Current SuperAdmin user
            
        Returns:
            List of users
        """
        return user_management_db_crud.get_users(db=db, skip=skip, limit=limit)
    
    async def get_user(self, db: Session, user_id: int, current_user: User) -> User:
        """
        Get user by ID
        
        Args:
            db: Database session
            user_id: User ID to retrieve
            current_user: Current SuperAdmin user
            
        Returns:
            User information
            
        Raises:
            HTTPException: If user not found
        """
        user = user_management_db_crud.get_user_by_id(db=db, user_id=user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )
        
        return user
    
    async def update_user(self, db: Session, user_id: int, user_update: UserUpdate, current_user: User) -> User:
        """
        Update user by ID
        
        Args:
            db: Database session
            user_id: User ID to update
            user_update: User update data
            current_user: Current SuperAdmin user
            
        Returns:
            Updated user information
            
        Raises:
            HTTPException: If user not found or update fails
        """
        try:
            # Get existing user
            db_user = user_management_db_crud.get_user_by_id(db, user_id)
            if not db_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with ID {user_id} not found"
                )
            
            # Check username uniqueness (if being updated)
            if user_update.username and user_update.username != db_user.username:
                existing_user = user_management_db_crud.get_user_by_username(db, user_update.username)
                if existing_user and existing_user.user_id != user_id:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Username '{user_update.username}' already exists"
                    )
            
            # Check email uniqueness (if being updated)
            if user_update.email and user_update.email != db_user.email:
                existing_user = user_management_db_crud.get_user_by_email(db, user_update.email)
                if existing_user and existing_user.user_id != user_id:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Email '{user_update.email}' already exists"
                    )
            
            # Verify role exists (if being updated)
            if user_update.role_name and user_update.role_name != db_user.role_name:
                role = user_management_db_crud.get_role_by_name(db, user_update.role_name)
                if not role:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Role with name '{user_update.role_name}' not found"
                    )
            
            # Update user
            updated_user = user_management_db_crud.update_user(
                db=db,
                db_user=db_user,
                user_update=user_update
            )
            
            # Commit transaction
            db.commit()
            db.refresh(updated_user)
            
            return updated_user
            
        except HTTPException:
            db.rollback()
            raise
        except ValueError as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update user: {str(e)}"
            )
    
    async def delete_user(self, db: Session, user_id: int, current_user: User) -> dict:
        """
        Delete user by ID
        
        Args:
            db: Database session
            user_id: User ID to delete
            current_user: Current SuperAdmin user
            
        Returns:
            Confirmation message
            
        Raises:
            HTTPException: If user not found or cannot be deleted
        """
        try:
            # Prevent SuperAdmin from deleting themselves
            if user_id == current_user.user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot delete your own account"
                )
            
            # Get user to delete
            db_user = user_management_db_crud.get_user_by_id(db, user_id)
            if not db_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with ID {user_id} not found"
                )
            
            # Delete user
            user_management_db_crud.delete_user(db, db_user)
            
            # Commit transaction
            db.commit()
            
            return {"message": f"User with ID {user_id} has been deleted successfully"}
            
        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete user: {str(e)}"
            )

    async def update_user_status_by_username(self, db: Session, username: str, is_active: bool, current_user: User) -> dict:
        """
        Update user active status by username (activate or deactivate)
        
        Args:
            db: Database session
            username: Username to update
            is_active: New active status (True=activate, False=deactivate)
            current_user: Current SuperAdmin user
            
        Returns:
            Confirmation message and user info
            
        Raises:
            HTTPException: If user not found or cannot be updated
        """
        try:
            # Prevent SuperAdmin from deactivating themselves
            if username == current_user.username and not is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot deactivate your own account"
                )
            
            # Get user to update
            db_user = user_management_db_crud.get_user_by_username(db, username)
            if not db_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with username '{username}' not found"
                )
            
            # Check if user status is already the same
            if db_user.is_active == is_active:
                status_text = "activated" if is_active else "deactivated"
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"User '{username}' is already {status_text}"
                )
            
            # Update user status
            db_user.is_active = is_active
            db.add(db_user)
            
            # Commit transaction
            db.commit()
            db.refresh(db_user)
            
            action = "activated" if is_active else "deactivated"
            return {
                "message": f"User '{username}' has been {action} successfully",
                "user": {
                    "user_id": db_user.user_id,
                    "username": db_user.username,
                    "email": db_user.email,
                    "role_name": db_user.role_name,
                    "is_active": db_user.is_active
                }
            }
            
        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update user status: {str(e)}"
            )


# Global logic instance
user_management_logic = UserManagementLogic()