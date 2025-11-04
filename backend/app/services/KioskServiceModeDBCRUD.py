# KioskServiceModeDBCRUD.py
# Database CRUD operations for kiosk service mode management
# NOTE: This layer does not perform commit/rollback.
# Transaction management is in the Logic layer.

from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..database.models import KioskServiceMode, User
from ..models.KioskServiceModePydanticModel import ServiceModeRequest


class KioskServiceModeDBCRUD:
    """Database CRUD operations for kiosk service mode management"""
    
    def get_service_mode_by_kiosk_username(self, db: Session, kiosk_username: str) -> Optional[KioskServiceMode]:
        """
        Get service mode record by kiosk username
        
        Args:
            db: Database session
            kiosk_username: Kiosk username to search for
            
        Returns:
            KioskServiceMode object if found, None otherwise
        """
        return db.query(KioskServiceMode).filter(
            KioskServiceMode.kiosk_username == kiosk_username
        ).first()
    
    def get_all_service_mode_statuses(self, db: Session) -> List[KioskServiceMode]:
        """
        Get all kiosk service mode statuses
        
        Args:
            db: Database session
            
        Returns:
            List of all KioskServiceMode objects
        """
        return db.query(KioskServiceMode).all()
    
    def get_kiosks_in_service_mode(self, db: Session) -> List[KioskServiceMode]:
        """
        Get all kiosks currently in service mode
        
        Args:
            db: Database session
            
        Returns:
            List of KioskServiceMode objects where is_service_mode is True
        """
        return db.query(KioskServiceMode).filter(
            KioskServiceMode.is_service_mode == True
        ).all()
    
    def get_active_kiosk_users(self, db: Session) -> List[User]:
        """
        Get all active kiosk users
        
        Args:
            db: Database session
            
        Returns:
            List of active User objects with role 'kiosk'
        """
        return db.query(User).filter(
            User.role_name == "kiosk",
            User.is_active == True
        ).all()
    
    def update_service_mode_status(
        self, 
        db: Session, 
        kiosk_username: str, 
        is_service_mode: bool, 
        service_picture_name: Optional[str] = None
    ) -> Optional[KioskServiceMode]:
        """
        Update service mode status for a kiosk
        
        Args:
            db: Database session
            kiosk_username: Kiosk username to update
            is_service_mode: New service mode status
            service_picture_name: Service picture name (cleared if deactivating)
            
        Returns:
            Updated KioskServiceMode object if found, None otherwise
        """
        service_mode_record = self.get_service_mode_by_kiosk_username(db, kiosk_username)
        
        if not service_mode_record:
            return None
        
        # Update service mode status
        service_mode_record.is_service_mode = is_service_mode
        
        # Set or clear service picture name based on service mode status
        if is_service_mode:
            service_mode_record.service_picture_name = service_picture_name
        else:
            service_mode_record.service_picture_name = None
        
        # Flush changes (no commit)
        db.flush()
        
        return service_mode_record
    
    def bulk_update_service_mode_status(
        self, 
        db: Session, 
        kiosk_usernames: List[str], 
        is_service_mode: bool, 
        service_picture_name: Optional[str] = None
    ) -> List[KioskServiceMode]:
        """
        Update service mode status for multiple kiosks
        
        Args:
            db: Database session
            kiosk_usernames: List of kiosk usernames to update
            is_service_mode: New service mode status
            service_picture_name: Service picture name (cleared if deactivating)
            
        Returns:
            List of updated KioskServiceMode objects
        """
        updated_records = []
        
        for kiosk_username in kiosk_usernames:
            updated_record = self.update_service_mode_status(
                db, kiosk_username, is_service_mode, service_picture_name
            )
            if updated_record:
                updated_records.append(updated_record)
        
        return updated_records
    
    def get_kiosk_user_by_username(self, db: Session, kiosk_username: str) -> Optional[User]:
        """
        Get kiosk user by username
        
        Args:
            db: Database session
            kiosk_username: Kiosk username to search for
            
        Returns:
            User object if found and is a kiosk user, None otherwise
        """
        return db.query(User).filter(
            User.username == kiosk_username,
            User.role_name == "kiosk"
        ).first()
    
    def get_service_mode_statistics(self, db: Session) -> Dict[str, int]:
        """
        Get service mode statistics
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with service mode statistics
        """
        total_kiosks = db.query(KioskServiceMode).count()
        
        active_kiosks = db.query(KioskServiceMode).join(User).filter(
            User.role_name == "kiosk",
            User.is_active == True
        ).count()
        
        kiosks_in_service_mode = db.query(KioskServiceMode).filter(
            KioskServiceMode.is_service_mode == True
        ).count()
        
        return {
            "total_kiosks": total_kiosks,
            "active_kiosks": active_kiosks,
            "kiosks_in_service_mode": kiosks_in_service_mode,
            "inactive_kiosks": total_kiosks - active_kiosks
        }
    
    def validate_kiosk_usernames_exist(self, db: Session, kiosk_usernames: List[str]) -> Dict[str, bool]:
        """
        Validate that kiosk usernames exist and are active
        
        Args:
            db: Database session
            kiosk_usernames: List of kiosk usernames to validate
            
        Returns:
            Dictionary mapping username to existence/active status
        """
        validation_results = {}
        
        for kiosk_username in kiosk_usernames:
            kiosk_user = self.get_kiosk_user_by_username(db, kiosk_username)
            validation_results[kiosk_username] = kiosk_user is not None and kiosk_user.is_active
        
        return validation_results


# Global service instance
kiosk_service_mode_db_crud = KioskServiceModeDBCRUD()