# SuperAdminInit.py
# Dedicated endpoint for first-time SuperAdmin creation with race condition protection

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.SuperAdminInitPydanticModel import SuperAdminSetupRequest, SetupStatusResponse
from ..models.AuthenticationEndpointsPydanticModel import LoginResponse
from ..logic.SuperAdminInitLogic import superadmin_init_logic

# Create router for first-time SuperAdmin setup
router = APIRouter(prefix="/setup", tags=["first-time-setup"])


@router.post("/superadmin", response_model=LoginResponse)
async def create_first_superadmin(
    setup_request: SuperAdminSetupRequest,
    db: Session = Depends(get_db)
):
    """
    First-time SuperAdmin creation endpoint with race condition protection.
    
    This endpoint is specifically designed to handle the initial SuperAdmin creation
    safely, even under concurrent requests. It uses database-level constraints
    and atomic operations to prevent multiple SuperAdmins.
    
    Args:
        setup_request: SuperAdmin creation request with credentials
        db: Database session
        
    Returns:
        Login response with access token and user info
        
    Raises:
        HTTPException: If SuperAdmin already exists or creation fails
    """
    return await superadmin_init_logic.create_first_superadmin(db, setup_request)


@router.get("/status", response_model=SetupStatusResponse)
async def check_setup_status(db: Session = Depends(get_db)):
    """
    Check if the system needs initial SuperAdmin setup.
    
    This endpoint can be called without authentication to determine
    if first-time setup is required.
    
    Args:
        db: Database session
        
    Returns:
        Dictionary indicating whether setup is needed
    """
    return await superadmin_init_logic.check_setup_status(db)