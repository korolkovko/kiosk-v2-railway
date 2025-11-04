# UserManagement.py
# User management endpoints (only accessible by SuperAdmin)

from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models.UserManagementPydanticModel import UserCreate, UserResponse, UserUpdate, AdminCreate
from ..auth import get_current_superadmin
from ..logic.UserManagementLogic import user_management_logic
from ..database.models import User

# Create router for user management endpoints
router = APIRouter(prefix="/users", tags=["user-management"])


@router.post("/create-admin", response_model=UserResponse)
async def create_admin_user(
    user_data: AdminCreate,
    current_user: User = Depends(get_current_superadmin),
    db: Session = Depends(get_db)
):
    """
    Create a new Admin user. Only accessible by SuperAdmin.
    
    Logic:
    1. Verify requester is SuperAdmin (handled by dependency)
    2. Check if 'admin' role exists in roles table
    3. Assign admin role_name from roles table to new user (ignores role_id in request)
    4. Return success/failure message
    
    Args:
        user_data: User creation data (role_id field is ignored - admin role assigned automatically)
        current_user: Current SuperAdmin user (verified)
        db: Database session
        
    Returns:
        Created admin user information
        
    Raises:
        HTTPException: If admin role not found or user creation fails
    """
    admin_user = await user_management_logic.create_admin_user(db, user_data, current_user)
    return UserResponse.model_validate(admin_user)


@router.get("/", response_model=List[UserResponse])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_superadmin),
    db: Session = Depends(get_db)
):
    """
    Get list of all users. Only accessible by SuperAdmin.
    
    Args:
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        current_user: Current SuperAdmin user
        db: Database session
        
    Returns:
        List of users
    """
    users = await user_management_logic.get_users(db, skip, limit, current_user)
    return [UserResponse.model_validate(user) for user in users]


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_superadmin),
    db: Session = Depends(get_db)
):
    """
    Get user by ID. Only accessible by SuperAdmin.
    
    Args:
        user_id: User ID to retrieve
        current_user: Current SuperAdmin user
        db: Database session
        
    Returns:
        User information
        
    Raises:
        HTTPException: If user not found
    """
    user = await user_management_logic.get_user(db, user_id, current_user)
    return UserResponse.model_validate(user)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_superadmin),
    db: Session = Depends(get_db)
):
    """
    Update user by ID. Only accessible by SuperAdmin.
    
    Args:
        user_id: User ID to update
        user_update: User update data
        current_user: Current SuperAdmin user
        db: Database session
        
    Returns:
        Updated user information
        
    Raises:
        HTTPException: If user not found or update fails
    """
    updated_user = await user_management_logic.update_user(db, user_id, user_update, current_user)
    return UserResponse.model_validate(updated_user)


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_superadmin),
    db: Session = Depends(get_db)
):
    """
    Delete user by ID. Only accessible by SuperAdmin.
    
    Args:
        user_id: User ID to delete
        current_user: Current SuperAdmin user
        db: Database session
        
    Returns:
        Confirmation message
        
    Raises:
        HTTPException: If user not found or cannot be deleted
    """
    return await user_management_logic.delete_user(db, user_id, current_user)


@router.patch("/status/{username}")
async def update_user_status_by_username(
    username: str,
    is_active: bool = Body(..., description="Set user active status: true to activate, false to deactivate"),
    current_user: User = Depends(get_current_superadmin),
    db: Session = Depends(get_db)
):
    """
    Update user active status by username. Only accessible by SuperAdmin.
    Can both activate (is_active=true) and deactivate (is_active=false) users.
    
    Args:
        username: Username to update
        is_active: New active status (true=activate, false=deactivate)
        current_user: Current SuperAdmin user
        db: Database session
        
    Returns:
        Confirmation message and updated user info
        
    Raises:
        HTTPException: If user not found or cannot be updated
    """
    return await user_management_logic.update_user_status_by_username(db, username, is_active, current_user)