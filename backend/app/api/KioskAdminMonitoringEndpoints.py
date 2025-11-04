# KioskAdminMonitoringEndpoints.py
# FastAPI endpoints for admin monitoring of kiosk devices and telemetry
# Provides administrative oversight of kiosk authentication and device status

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from ..database.connection import get_db, engine
from ..database.models import User
from ..auth.dependencies import get_current_superadmin
from ..services.kiosk_device_registry_crud import kiosk_device_registry_crud


router = APIRouter(
    prefix="/admin/kiosk",
    tags=["Kiosk Admin Monitoring"]
)


@router.get("/devices/telemetry", status_code=status.HTTP_200_OK)
async def get_all_kiosk_devices_telemetry(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superadmin),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return")
):
    """
    Get telemetry data for all kiosk devices (SuperAdmin only)
    
    Provides comprehensive overview of all kiosk devices including their
    last activity, status, and basic information for administrative monitoring.
    
    Args:
        db: Database session
        current_user: Current SuperAdmin user
        skip: Number of records to skip for pagination
        limit: Maximum number of records to return
        
    Returns:
        List of dictionaries with kiosk device telemetry information
    """
    telemetry_data = await kiosk_device_registry_crud.get_all_kiosk_devices_telemetry(
        db=db, skip=skip, limit=limit
    )
    
    return {
        "success": True,
        "total_records": len(telemetry_data),
        "skip": skip,
        "limit": limit,
        "kiosk_devices": telemetry_data,
        "message": "Kiosk devices telemetry retrieved successfully"
    }


@router.get("/devices/{kiosk_username}/telemetry", status_code=status.HTTP_200_OK)
async def get_kiosk_device_telemetry(
    kiosk_username: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superadmin)
):
    """
    Get telemetry data for specific kiosk device (SuperAdmin only)
    
    Args:
        kiosk_username: Username of the kiosk to get telemetry for
        db: Database session
        current_user: Current SuperAdmin user
        
    Returns:
        Dictionary with specific kiosk device telemetry information
    """
    telemetry_data = await kiosk_device_registry_crud.get_kiosk_device_telemetry(
        db=db, kiosk_username=kiosk_username
    )
    
    if "error" in telemetry_data:
        return {
            "success": False,
            "error": telemetry_data["error"],
            "kiosk_username": kiosk_username
        }
    
    return {
        "success": True,
        "kiosk_username": kiosk_username,
        "telemetry": telemetry_data,
        "message": f"Telemetry for kiosk '{kiosk_username}' retrieved successfully"
    }


@router.get("/activity/summary", status_code=status.HTTP_200_OK)
async def get_kiosk_activity_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superadmin)
):
    """
    Get summary of kiosk activity for admin dashboard (SuperAdmin only)
    
    Provides high-level metrics about kiosk activity including total counts,
    active devices, and recent activity statistics.
    
    Args:
        db: Database session
        current_user: Current SuperAdmin user
        
    Returns:
        Dictionary with kiosk activity summary metrics
    """
    activity_summary = await kiosk_device_registry_crud.get_kiosk_activity_summary(db)
    
    return {
        "success": True,
        "activity_summary": activity_summary,
        "message": "Kiosk activity summary retrieved successfully"
    }


@router.get("/sessions/active/count", status_code=status.HTTP_200_OK)
async def get_active_kiosk_sessions_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superadmin)
):
    """
    Get count of active kiosk sessions (SuperAdmin only)
    
    Args:
        db: Database session
        current_user: Current SuperAdmin user
        
    Returns:
        Dictionary with active kiosk sessions count
    """
    active_count = await kiosk_device_registry_crud.get_active_kiosk_sessions_count(db)
    
    return {
        "success": True,
        "active_kiosk_sessions": active_count,
        "message": f"Found {active_count} active kiosk sessions"
    }


@router.get("/users/list", status_code=status.HTTP_200_OK)
async def get_all_kiosk_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superadmin),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    active_only: bool = Query(False, description="Return only active kiosk users")
):
    """
    Get list of all kiosk users for admin management (SuperAdmin only)
    
    Args:
        db: Database session
        current_user: Current SuperAdmin user
        skip: Number of records to skip for pagination
        limit: Maximum number of records to return
        active_only: Filter to return only active users
        
    Returns:
        List of kiosk users with their information
    """
    query = db.query(User).filter(User.role_name == "kiosk")
    
    if active_only:
        query = query.filter(User.is_active == True)
    
    kiosk_users = query.offset(skip).limit(limit).all()
    
    users_data = []
    for user in kiosk_users:
        users_data.append({
            "user_id": user.user_id,
            "username": user.username,
            "email": user.email,
            "phone": user.phone,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
            "last_login_at": user.last_login_at,
            "role_name": user.role_name
        })
    
    return {
        "success": True,
        "total_records": len(users_data),
        "skip": skip,
        "limit": limit,
        "active_only": active_only,
        "kiosk_users": users_data,
        "message": "Kiosk users list retrieved successfully"
    }


@router.put("/users/{kiosk_username}/status", status_code=status.HTTP_200_OK)
async def update_kiosk_user_status(
    kiosk_username: str,
    is_active: bool,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superadmin)
):
    """
    Update kiosk user active status (SuperAdmin only)
    
    Allows SuperAdmin to activate or deactivate kiosk users, which will
    prevent them from authenticating if deactivated.
    
    Args:
        kiosk_username: Username of the kiosk user to update
        is_active: New active status (True=activate, False=deactivate)
        db: Database session
        current_user: Current SuperAdmin user
        
    Returns:
        Dictionary with update confirmation and user info
    """
    try:
        # Find the kiosk user
        kiosk_user = db.query(User).filter(
            User.username == kiosk_username,
            User.role_name == "kiosk"
        ).first()

        if not kiosk_user:
            return {
                "success": False,
                "error": f"Kiosk user '{kiosk_username}' not found",
                "kiosk_username": kiosk_username
            }

        # Check if status is already the same
        if kiosk_user.is_active == is_active:
            status_text = "active" if is_active else "inactive"
            return {
                "success": False,
                "error": f"Kiosk user '{kiosk_username}' is already {status_text}",
                "kiosk_username": kiosk_username,
                "current_status": kiosk_user.is_active
            }

        # Update status
        kiosk_user.is_active = is_active
        db.add(kiosk_user)
        db.commit()
        db.refresh(kiosk_user)

        action = "activated" if is_active else "deactivated"
        return {
            "success": True,
            "message": f"Kiosk user '{kiosk_username}' has been {action} successfully",
            "kiosk_user": {
                "user_id": kiosk_user.user_id,
                "username": kiosk_user.username,
                "is_active": kiosk_user.is_active,
                "role_name": kiosk_user.role_name,
                "updated_at": kiosk_user.updated_at
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update kiosk user status: {str(e)}"
        )


# Future extensibility endpoints

@router.get("/infrastructure/prepare-tables", status_code=status.HTTP_200_OK)
async def get_infrastructure_preparation_sql(
    current_user: User = Depends(get_current_superadmin)
):
    """
    Get SQL statements for preparing future kiosk infrastructure tables (SuperAdmin only)
    
    Returns SQL statements that can be used to create dedicated device registry
    and token deny-list tables when needed for future extensibility.
    
    Args:
        current_user: Current SuperAdmin user
        
    Returns:
        Dictionary with SQL statements for infrastructure preparation
    """
    device_registry_sql = await kiosk_device_registry_crud.prepare_device_registry_table_creation()
    deny_list_sql = await kiosk_device_registry_crud.prepare_token_deny_list_table_creation()
    
    return {
        "success": True,
        "infrastructure_sql": {
            "device_registry": device_registry_sql,
            "token_deny_list": deny_list_sql
        },
        "message": "Infrastructure preparation SQL retrieved successfully",
        "note": "These SQL statements are for future extensibility and are not currently required"
    }


@router.get("/tokens/{jti}/deny-list-status", status_code=status.HTTP_200_OK)
async def check_token_deny_list_status(
    jti: str,
    current_user: User = Depends(get_current_superadmin)
):
    """
    Check token deny-list status (placeholder for future functionality)
    
    Args:
        jti: JWT token ID to check
        current_user: Current SuperAdmin user
        
    Returns:
        Dictionary with token deny-list status
    """
    status_info = await kiosk_device_registry_crud.check_token_deny_list_status(jti)
    
    return {
        "success": True,
        "jti": jti,
        "deny_list_status": status_info,
        "message": "Token deny-list status checked (functionality not yet implemented)"
    }


@router.get("/database/pool-status", status_code=status.HTTP_200_OK)
async def get_database_pool_status(
    current_user: User = Depends(get_current_superadmin)
):
    """
    Get database connection pool status and health metrics (SuperAdmin only)

    Returns real-time information about SQLAlchemy connection pool including:
    - Current connections in use vs available
    - Overflow connection usage
    - Pool utilization percentages
    - Health warnings if pool is near exhaustion

    Args:
        current_user: Current SuperAdmin user

    Returns:
        Dictionary with connection pool status and health diagnostics
    """
    pool = engine.pool

    # Get pool configuration
    pool_size = pool.size()
    checked_out = pool.checkedout()
    overflow = pool.overflow()

    # Calculate metrics
    in_pool = max(0, pool_size - checked_out)
    pool_utilization = round((checked_out / pool_size) * 100, 2) if pool_size > 0 else 0
    overflow_utilization = round((overflow / pool._max_overflow) * 100, 2) if pool._max_overflow > 0 else 0

    # Health check
    healthy = True
    warnings = []

    if pool_utilization >= 90:
        healthy = False
        warnings.append({
            "severity": "critical",
            "message": f"Pool utilization critical: {pool_utilization}%",
            "recommendation": "Increase pool_size or investigate connection leaks immediately"
        })
    elif pool_utilization >= 80:
        warnings.append({
            "severity": "warning",
            "message": f"Pool utilization high: {pool_utilization}%",
            "recommendation": "Monitor closely and consider increasing pool_size"
        })

    if overflow > 0:
        if overflow_utilization >= 90:
            healthy = False
            warnings.append({
                "severity": "critical",
                "message": f"Overflow utilization critical: {overflow_utilization}%",
                "recommendation": "Pool exhaustion imminent - increase pool_size and max_overflow"
            })
        elif overflow_utilization >= 50:
            warnings.append({
                "severity": "warning",
                "message": f"Using overflow connections: {overflow}/{pool._max_overflow}",
                "recommendation": "Consider increasing pool_size to reduce overflow usage"
            })

    return {
        "success": True,
        "healthy": healthy,
        "pool_status": {
            "pool_size": pool_size,
            "max_overflow": pool._max_overflow,
            "connections_in_pool": in_pool,
            "connections_in_use": checked_out,
            "connections_overflow": overflow,
            "total_connections": checked_out + overflow,
            "pool_utilization_percent": pool_utilization,
            "overflow_utilization_percent": overflow_utilization
        },
        "warnings": warnings,
        "message": "Database pool status retrieved successfully"
    }


@router.get("/health/monitoring", status_code=status.HTTP_200_OK)
async def kiosk_monitoring_health_check(
    current_user: User = Depends(get_current_superadmin)
):
    """
    Health check endpoint for kiosk monitoring service

    Args:
        current_user: Current SuperAdmin user

    Returns:
        Dictionary with monitoring service health status
    """
    return {
        "service": "kiosk_admin_monitoring",
        "status": "healthy",
        "version": "1.0.0",
        "features": {
            "device_telemetry": True,
            "activity_summary": True,
            "user_management": True,
            "infrastructure_preparation": True,
            "deny_list_ready": False,
            "database_pool_monitoring": True
        },
        "message": "Kiosk admin monitoring service is operational"
    }