# KioskServiceModeEndpoint.py
# API endpoints for kiosk service mode management
# Allows admin/superadmin users to activate/deactivate service mode on multiple kiosks

from fastapi import APIRouter, Depends, status, HTTPException, Query, Path
from sqlalchemy.orm import Session

from ..auth.dependencies import get_current_admin, get_db
from ..auth.kiosk_dependencies import get_current_kiosk_user, get_current_kiosk_username
from ..models.KioskServiceModePydanticModel import (
    ServiceModeRequest, 
    ServiceModeOperationResult,
    KioskServiceModeStatus,
    ServiceModeStatusListResponse
)
from ..logic.KioskServiceModeLogic import kiosk_service_mode_logic
from ..database.models import User

router = APIRouter(
    prefix="/kiosk/service-mode",
    tags=["Kiosk Service Mode"]
)


@router.get(
    "/kiosk-status-for-kiosk-user",
    status_code=status.HTTP_200_OK,
    summary="Get service mode status for current kiosk",
    description="Allows kiosk users to check their own service mode status",
    responses={
        200: {
            "description": "Service mode status retrieved successfully",
            "content": {
                "application/json": {
                    "examples": {
                        "normal_operation": {
                            "summary": "Normal operation mode",
                            "value": {
                                "kiosk_username": "kiosk_001",
                                "is_service_mode": False,
                                "service_picture_name": None,
                                "message": "Kiosk is in normal operation mode"
                            }
                        },
                        "service_mode_active": {
                            "summary": "Service mode active",
                            "value": {
                                "kiosk_username": "kiosk_001",
                                "is_service_mode": True,
                                "service_picture_name": "maintenance",
                                "message": "Kiosk is in service mode"
                            }
                        }
                    }
                }
            }
        },
        401: {"description": "Unauthorized (invalid kiosk token)"},
        404: {"description": "Service mode record not found"},
        500: {"description": "Internal server error"}
    },
    tags=["Kiosk Self-Service"]
)
async def get_kiosk_status_for_kiosk_user(
    current_user: User = Depends(get_current_kiosk_user),
    kiosk_username: str = Depends(get_current_kiosk_username),
    db: Session = Depends(get_db)
):
    """
    **Get current service mode status for this kiosk**
    
    This endpoint allows kiosk users to check their own service mode status.
    Kiosks should call this endpoint on login/startup to determine if they
    should display the service mode screen or operate normally.
    
    **Use Cases:**
    - Check service mode status on kiosk login/startup
    - Periodic status checks for service mode changes
    - Determine which service picture to display
    - Fallback check if SSE connection is lost
    
    **Behavior:**
    - Returns current service mode status for the authenticated kiosk
    - If no service mode record exists, creates one with default values
    - Only accessible by authenticated kiosk users
    - Does not require admin privileges
    
    **Integration:**
    - Call this endpoint after successful kiosk login
    - Use in combination with SSE events for real-time updates
    - Frontend should respect the service mode status immediately
    
    **Access:** Available to authenticated kiosk users only
    """
    try:
        from ..services.KioskServiceModeDBCRUD import kiosk_service_mode_db_crud
        
        # Get service mode record for this kiosk
        service_mode_record = kiosk_service_mode_db_crud.get_service_mode_by_kiosk_username(
            db, kiosk_username
        )
        
        if not service_mode_record:
            # If no record exists, create one with default values
            from ..database.models import KioskServiceMode
            service_mode_record = KioskServiceMode(
                kiosk_username=kiosk_username,
                is_service_mode=False,
                service_picture_name=None
            )
            db.add(service_mode_record)
            db.commit()
            db.refresh(service_mode_record)
        
        message = "Kiosk is in service mode" if service_mode_record.is_service_mode else "Kiosk is in normal operation mode"
        
        return {
            "kiosk_username": service_mode_record.kiosk_username,
            "is_service_mode": service_mode_record.is_service_mode,
            "service_picture_name": service_mode_record.service_picture_name,
            "message": message
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get service mode status: {str(e)}"
        )


@router.get(
    "/status",
    response_model=ServiceModeStatusListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get service mode status for all kiosks",
    description="Get comprehensive service mode information for all registered kiosks",
    responses={
        200: {
            "description": "Service mode statuses retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "kiosks": [
                            {
                                "kiosk_username": "kiosk_001",
                                "is_service_mode": True,
                                "service_picture_name": "maintenance",
                                "is_kiosk_active": True,
                                "has_active_sse_connection": True
                            },
                            {
                                "kiosk_username": "kiosk_002",
                                "is_service_mode": False,
                                "service_picture_name": None,
                                "is_kiosk_active": True,
                                "has_active_sse_connection": False
                            }
                        ],
                        "total_kiosks": 3,
                        "active_kiosks": 3,
                        "kiosks_in_service_mode": 1
                    }
                }
            }
        },
        403: {"description": "Admin access required"}
    }
)
async def get_all_service_mode_statuses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    **Get service mode status for all kiosks**
    
    Returns comprehensive service mode information for all registered kiosks,
    including their current status, active connections, and system statistics.
    
    **Response includes:**
    - Individual kiosk service mode statuses
    - Whether each kiosk user is active
    - SSE connection status for each kiosk
    - Overall system statistics
    
    **Use cases:**
    - Monitor which kiosks are currently in service mode
    - Check kiosk connectivity before sending service mode commands
    - Get overview of system-wide service mode status
    - Troubleshoot service mode issues
    
    **Access:** Available to admin and superadmin roles only
    """
    return await kiosk_service_mode_logic.get_all_service_mode_statuses(
        db=db, 
        current_user=current_user
    )


@router.get(
    "/kiosk-status-for-admin-user/{kiosk_username}",
    response_model=KioskServiceModeStatus,
    status_code=status.HTTP_200_OK,
    summary="Get service mode status for specific kiosk",
    description="Get detailed service mode information for a single kiosk by username",
    responses={
        200: {
            "description": "Service mode status retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "kiosk_username": "kiosk_001",
                        "is_service_mode": True,
                        "service_picture_name": "maintenance",
                        "is_kiosk_active": True,
                        "has_active_sse_connection": True
                    }
                }
            }
        },
        404: {"description": "Kiosk username not found"},
        403: {"description": "Admin access required"}
    }
)
async def get_kiosk_status_for_admin_user(
    kiosk_username: str = Path(
        ...,
        description="Kiosk username to get service mode status for (e.g., kiosk_001)",
        example="kiosk_001"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    **Get service mode status for a specific kiosk**
    
    Returns detailed service mode information for a single kiosk,
    including current status, connectivity, and configuration.
    
    **Path Parameters:**
    - `kiosk_username`: Username of the kiosk to check (e.g., "kiosk_001")
    
    **Response includes:**
    - Current service mode status (active/inactive)
    - Service picture name (if in service mode)
    - Kiosk user active status
    - SSE connection status
    
    **Example Usage:**
    ```
    GET /api/v1/kiosk/service-mode/status/kiosk_001
    ```
    
    **Access:** Available to admin and superadmin roles only
    """
    return await kiosk_service_mode_logic.get_service_mode_status_for_kiosk(
        db=db, 
        kiosk_username=kiosk_username, 
        current_user=current_user
    )


@router.post(
    "/activate",
    response_model=ServiceModeOperationResult,
    status_code=status.HTTP_200_OK,
    summary="Activate service mode on multiple kiosks",
    description="Convenience endpoint to quickly activate service mode on specified kiosks with a service picture",
    responses={
        200: {
            "description": "Service mode activation completed",
            "content": {
                "application/json": {
                    "example": {
                        "total_requested": 2,
                        "successful_updates": 2,
                        "ignored_kiosks": 0,
                        "failed_updates": 0,
                        "results": [
                            {
                                "kiosk_username": "kiosk_001",
                                "is_service_mode": True,
                                "service_picture_name": "maintenance",
                                "status": "updated",
                                "message": "Service mode activated successfully"
                            }
                        ]
                    }
                }
            }
        },
        400: {"description": "Invalid parameters or missing required fields"},
        403: {"description": "Admin access required"}
    }
)
async def activate_service_mode(
    kiosk_usernames: list[str] = Query(
        ...,
        description="List of kiosk usernames to activate service mode for. Each username should be a valid kiosk user (e.g., kiosk_001, kiosk_002)",
        example=["kiosk_001", "kiosk_002"],
        alias="kiosk_usernames"
    ),
    service_picture_name: str = Query(
        ...,
        description="Name of service picture to display on kiosks. Common values: maintenance, cleaning, technical, closed",
        example="maintenance",
        min_length=1,
        max_length=100
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    **Activate service mode on multiple kiosks**
    
    Convenience endpoint for quickly activating service mode without requiring
    a full JSON request body. Useful for emergency maintenance activation.
    
    **Query Parameters:**
    - `kiosk_usernames`: List of kiosk usernames (repeat parameter for multiple values)
    - `service_picture_name`: Picture to display (e.g., "maintenance", "cleaning", "technical")
    
    **Example Usage:**
    ```
    POST /api/v1/kiosk/service-mode/activate?kiosk_usernames=kiosk_001&kiosk_usernames=kiosk_002&service_picture_name=maintenance
    ```
    
    **What Happens:**
    1. Service mode activated for specified kiosks
    2. Picture name stored in database
    3. SSE events sent to connected kiosks
    4. Kiosks display service mode screen immediately
    
    **Access:** Available to admin and superadmin roles only
    """
    request = ServiceModeRequest(
        kiosk_usernames=kiosk_usernames,
        is_service_mode=True,
        service_picture_name=service_picture_name
    )
    
    return await kiosk_service_mode_logic.update_service_mode_for_multiple_kiosks(
        db=db, 
        request=request, 
        current_user=current_user
    )


@router.post(
    "/deactivate",
    response_model=ServiceModeOperationResult,
    status_code=status.HTTP_200_OK,
    summary="Deactivate service mode on multiple kiosks",
    description="Convenience endpoint to quickly deactivate service mode and return kiosks to normal operation",
    responses={
        200: {
            "description": "Service mode deactivation completed",
            "content": {
                "application/json": {
                    "example": {
                        "total_requested": 2,
                        "successful_updates": 2,
                        "ignored_kiosks": 0,
                        "failed_updates": 0,
                        "results": [
                            {
                                "kiosk_username": "kiosk_001",
                                "is_service_mode": False,
                                "service_picture_name": None,
                                "status": "updated",
                                "message": "Service mode deactivated successfully"
                            }
                        ]
                    }
                }
            }
        },
        400: {"description": "Invalid parameters"},
        403: {"description": "Admin access required"}
    }
)
async def deactivate_service_mode(
    kiosk_usernames: list[str] = Query(
        ...,
        description="List of kiosk usernames to deactivate service mode for. Each username should be a valid kiosk user (e.g., kiosk_001, kiosk_002)",
        example=["kiosk_001", "kiosk_002"],
        alias="kiosk_usernames"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    **Deactivate service mode on multiple kiosks**
    
    Convenience endpoint for quickly deactivating service mode and returning
    kiosks to normal operation. Clears service picture and allows user interactions.
    
    **Query Parameters:**
    - `kiosk_usernames`: List of kiosk usernames (repeat parameter for multiple values)
    
    **Example Usage:**
    ```
    POST /api/v1/kiosk/service-mode/deactivate?kiosk_usernames=kiosk_001&kiosk_usernames=kiosk_002
    ```
    
    **What Happens:**
    1. Service mode deactivated for specified kiosks
    2. Picture name cleared from database
    3. SSE events sent to connected kiosks
    4. Kiosks return to normal operation immediately
    
    **Access:** Available to admin and superadmin roles only
    """
    request = ServiceModeRequest(
        kiosk_usernames=kiosk_usernames,
        is_service_mode=False,
        service_picture_name=None
    )
    
    return await kiosk_service_mode_logic.update_service_mode_for_multiple_kiosks(
        db=db, 
        request=request, 
        current_user=current_user
    )