# kiosk_device_registry_crud.py
# Database CRUD operations for kiosk device registry and telemetry tracking
# Provides lightweight device tracking for future extensibility

from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import HTTPException, status

from ..database.models import User
from ..models.kiosk_auth_models import (
    KioskDeviceRegistryCreate,
    KioskDeviceRegistryResponse,
    KioskTelemetryUpdate
)


class KioskDeviceRegistryCRUD:
    """CRUD operations for kiosk device registry and telemetry"""
    
    async def update_device_last_seen(
        self,
        db: Session,
        device_id: str,
        kiosk_username: str
    ) -> None:
        """
        Update device last seen timestamp for telemetry tracking
        
        Args:
            db: Database session
            device_id: Device identifier
            kiosk_username: Associated kiosk username
        """
        try:
            # For now, we'll use a simple approach without a dedicated device table
            # Update the user's last_login_at as a proxy for device activity
            user = db.query(User).filter(
                User.username == kiosk_username,
                User.role_name == "kiosk"
            ).first()
            
            if user:
                user.last_login_at = datetime.utcnow()
                db.add(user)
                # Note: Commit is handled by the calling logic layer
        except Exception as e:
            # Silently handle telemetry errors to not break authentication flow
            pass
    
    async def get_kiosk_device_telemetry(
        self,
        db: Session,
        kiosk_username: str
    ) -> Dict[str, Any]:
        """
        Get basic telemetry data for a kiosk device
        
        Args:
            db: Database session
            kiosk_username: Kiosk username to get telemetry for
            
        Returns:
            Dictionary with basic telemetry information
        """
        user = db.query(User).filter(
            User.username == kiosk_username,
            User.role_name == "kiosk"
        ).first()
        
        if not user:
            return {"error": "Kiosk user not found"}
        
        return {
            "kiosk_username": kiosk_username,
            "user_id": user.user_id,
            "is_active": user.is_active,
            "last_seen_at": user.last_login_at,
            "created_at": user.created_at,
            "updated_at": user.updated_at
        }
    
    async def get_all_kiosk_devices_telemetry(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get telemetry data for all kiosk devices
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of dictionaries with kiosk telemetry information
        """
        kiosk_users = db.query(User).filter(
            User.role_name == "kiosk"
        ).offset(skip).limit(limit).all()
        
        telemetry_data = []
        for user in kiosk_users:
            telemetry_data.append({
                "kiosk_username": user.username,
                "user_id": user.user_id,
                "is_active": user.is_active,
                "last_seen_at": user.last_login_at,
                "created_at": user.created_at,
                "updated_at": user.updated_at,
                "email": user.email,
                "phone": user.phone
            })
        
        return telemetry_data
    
    async def get_active_kiosk_sessions_count(self, db: Session) -> int:
        """
        Get count of active kiosk users (basic metric)
        
        Args:
            db: Database session
            
        Returns:
            Number of active kiosk users
        """
        count = db.query(User).filter(
            User.role_name == "kiosk",
            User.is_active == True
        ).count()
        
        return count
    
    async def get_kiosk_activity_summary(self, db: Session) -> Dict[str, Any]:
        """
        Get summary of kiosk activity for admin monitoring
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with activity summary
        """
        # Get basic counts
        total_kiosks = db.query(User).filter(User.role_name == "kiosk").count()
        active_kiosks = db.query(User).filter(
            User.role_name == "kiosk",
            User.is_active == True
        ).count()
        
        # Get recently active kiosks (last 24 hours)
        twenty_four_hours_ago = datetime.utcnow().replace(
            hour=datetime.utcnow().hour - 24
        )
        
        recently_active = db.query(User).filter(
            User.role_name == "kiosk",
            User.last_login_at >= twenty_four_hours_ago
        ).count()
        
        return {
            "total_kiosks": total_kiosks,
            "active_kiosks": active_kiosks,
            "inactive_kiosks": total_kiosks - active_kiosks,
            "recently_active_24h": recently_active,
            "last_updated": datetime.utcnow()
        }
    
    # Future extensibility methods for when dedicated device table is added
    
    async def prepare_device_registry_table_creation(self) -> Dict[str, str]:
        """
        Prepare SQL for future device registry table creation
        
        Returns:
            Dictionary with SQL statements for device registry table
        """
        return {
            "create_table_sql": """
                CREATE TABLE IF NOT EXISTS kiosk_device_registry (
                    registry_id SERIAL PRIMARY KEY,
                    device_id VARCHAR(100) UNIQUE NOT NULL,
                    device_name VARCHAR(200) NOT NULL,
                    location VARCHAR(200),
                    kiosk_username VARCHAR(100) REFERENCES users(username),
                    is_active BOOLEAN DEFAULT TRUE,
                    last_seen_at TIMESTAMP WITH TIME ZONE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """,
            "create_index_sql": """
                CREATE INDEX IF NOT EXISTS idx_device_registry_kiosk_username 
                ON kiosk_device_registry(kiosk_username);
                CREATE INDEX IF NOT EXISTS idx_device_registry_device_id 
                ON kiosk_device_registry(device_id);
                CREATE INDEX IF NOT EXISTS idx_device_registry_last_seen 
                ON kiosk_device_registry(last_seen_at);
            """
        }
    
    async def prepare_token_deny_list_table_creation(self) -> Dict[str, str]:
        """
        Prepare SQL for future token deny-list table creation
        
        Returns:
            Dictionary with SQL statements for token deny-list table
        """
        return {
            "create_table_sql": """
                CREATE TABLE IF NOT EXISTS kiosk_token_deny_list (
                    deny_id SERIAL PRIMARY KEY,
                    jti VARCHAR(36) UNIQUE NOT NULL,
                    kiosk_username VARCHAR(100),
                    denied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                    reason VARCHAR(200)
                );
            """,
            "create_index_sql": """
                CREATE INDEX IF NOT EXISTS idx_token_deny_list_jti 
                ON kiosk_token_deny_list(jti);
                CREATE INDEX IF NOT EXISTS idx_token_deny_list_expires 
                ON kiosk_token_deny_list(expires_at);
            """
        }
    
    async def check_token_deny_list_status(self, jti: str) -> Dict[str, Any]:
        """
        Check if token is in deny-list (placeholder for future implementation)
        
        Args:
            jti: JWT token ID to check
            
        Returns:
            Dictionary with deny-list status
        """
        return {
            "jti": jti,
            "is_denied": False,
            "message": "Token deny-list not yet implemented"
        }


# Global kiosk device registry CRUD instance
kiosk_device_registry_crud = KioskDeviceRegistryCRUD()