# KIOSKManagement.py

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ..auth.dependencies import get_current_superadmin, get_db
from ..models.UserManagementPydanticModel import KioskCreate, UserResponse
from ..logic.UserManagementLogic import user_management_logic
from ..database.models import User

router = APIRouter(
    prefix="/kiosk",
    tags=["Kiosk Management"]
)

@router.post("/create", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_kiosk_user(
    user_data: KioskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superadmin)
):
    return await user_management_logic.create_kiosk_user(db=db, user_data=user_data, current_user=current_user)