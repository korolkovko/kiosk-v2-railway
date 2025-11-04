# KioskServiceModeLogic.py
# Business logic for kiosk service mode operations
# NOTE: This layer manages full transaction: validation → operation → commit/rollback

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Dict, Any

from ..models.KioskServiceModePydanticModel import (
    ServiceModeRequest, 
    ServiceModeResponse, 
    ServiceModeOperationResult,
    KioskServiceModeStatus,
    ServiceModeStatusListResponse
)
from ..models.SSEEventModels import KioskServiceModeChangedEvent
from ..services.KioskServiceModeDBCRUD import kiosk_service_mode_db_crud
from ..database.models import User
from ..websockets.event_bus import bus


class KioskServiceModeLogic:
    """Business logic for kiosk service mode operations"""
    
    async def update_service_mode_for_multiple_kiosks(
        self, 
        db: Session, 
        request: ServiceModeRequest, 
        current_user: User
    ) -> ServiceModeOperationResult:
        """
        Update service mode status for multiple kiosks
        
        Args:
            db: Database session
            request: Service mode request with kiosk usernames and settings
            current_user: Current admin/superadmin user
            
        Returns:
            ServiceModeOperationResult with detailed results for each kiosk
            
        Raises:
            HTTPException: If validation fails or operation encounters errors
        """
        try:
            # Validate request
            if request.is_service_mode and not request.service_picture_name:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="service_picture_name is required when activating service mode"
                )
            
            # Validate kiosk usernames exist and are active
            validation_results = kiosk_service_mode_db_crud.validate_kiosk_usernames_exist(
                db, request.kiosk_usernames
            )
            
            results = []
            successful_updates = 0
            ignored_kiosks = 0
            failed_updates = 0
            
            # Process each kiosk
            for kiosk_username in request.kiosk_usernames:
                try:
                    if not validation_results.get(kiosk_username, False):
                        # Kiosk not found or inactive - ignore
                        results.append(ServiceModeResponse(
                            kiosk_username=kiosk_username,
                            is_service_mode=False,
                            service_picture_name=None,
                            status="ignored",
                            message="Kiosk not found or not active"
                        ))
                        ignored_kiosks += 1
                        continue
                    
                    # Update service mode status
                    updated_record = kiosk_service_mode_db_crud.update_service_mode_status(
                        db=db,
                        kiosk_username=kiosk_username,
                        is_service_mode=request.is_service_mode,
                        service_picture_name=request.service_picture_name if request.is_service_mode else None
                    )
                    
                    if updated_record:
                        # Create SSE event for this kiosk
                        await self._broadcast_service_mode_change_event(
                            kiosk_username=kiosk_username,
                            is_service_mode=request.is_service_mode,
                            service_picture_name=request.service_picture_name if request.is_service_mode else None
                        )
                        
                        action = "activated" if request.is_service_mode else "deactivated"
                        results.append(ServiceModeResponse(
                            kiosk_username=kiosk_username,
                            is_service_mode=updated_record.is_service_mode,
                            service_picture_name=updated_record.service_picture_name,
                            status="updated",
                            message=f"Service mode {action} successfully"
                        ))
                        successful_updates += 1
                    else:
                        results.append(ServiceModeResponse(
                            kiosk_username=kiosk_username,
                            is_service_mode=False,
                            service_picture_name=None,
                            status="error",
                            message="Failed to update service mode status"
                        ))
                        failed_updates += 1
                        
                except Exception as e:
                    results.append(ServiceModeResponse(
                        kiosk_username=kiosk_username,
                        is_service_mode=False,
                        service_picture_name=None,
                        status="error",
                        message=f"Error updating kiosk: {str(e)}"
                    ))
                    failed_updates += 1
            
            # Commit transaction if any updates were successful
            if successful_updates > 0:
                db.commit()
            else:
                db.rollback()
            
            return ServiceModeOperationResult(
                total_requested=len(request.kiosk_usernames),
                successful_updates=successful_updates,
                ignored_kiosks=ignored_kiosks,
                failed_updates=failed_updates,
                results=results
            )
            
        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update service mode: {str(e)}"
            )
    
    async def get_all_service_mode_statuses(self, db: Session, current_user: User) -> ServiceModeStatusListResponse:
        """
        Get service mode status for all kiosks
        
        Args:
            db: Database session
            current_user: Current admin/superadmin user
            
        Returns:
            ServiceModeStatusListResponse with all kiosk statuses
        """
        try:
            # Get all service mode records
            service_mode_records = kiosk_service_mode_db_crud.get_all_service_mode_statuses(db)
            
            # Get statistics
            stats = kiosk_service_mode_db_crud.get_service_mode_statistics(db)
            
            # Build response
            kiosk_statuses = []
            for record in service_mode_records:
                # Get kiosk user to check if active
                kiosk_user = kiosk_service_mode_db_crud.get_kiosk_user_by_username(db, record.kiosk_username)
                
                kiosk_statuses.append(KioskServiceModeStatus(
                    kiosk_username=record.kiosk_username,
                    is_service_mode=record.is_service_mode,
                    service_picture_name=record.service_picture_name,
                    is_kiosk_active=kiosk_user.is_active if kiosk_user else False,
                    has_active_sse_connection=await self._check_kiosk_has_active_sse_connection(record.kiosk_username)
                ))
            
            return ServiceModeStatusListResponse(
                kiosks=kiosk_statuses,
                total_kiosks=stats["total_kiosks"],
                active_kiosks=stats["active_kiosks"],
                kiosks_in_service_mode=stats["kiosks_in_service_mode"]
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get service mode statuses: {str(e)}"
            )
    
    async def get_service_mode_status_for_kiosk(
        self, 
        db: Session, 
        kiosk_username: str, 
        current_user: User
    ) -> KioskServiceModeStatus:
        """
        Get service mode status for a specific kiosk
        
        Args:
            db: Database session
            kiosk_username: Kiosk username to get status for
            current_user: Current admin/superadmin user
            
        Returns:
            KioskServiceModeStatus for the specified kiosk
            
        Raises:
            HTTPException: If kiosk not found
        """
        try:
            # Get service mode record
            service_mode_record = kiosk_service_mode_db_crud.get_service_mode_by_kiosk_username(db, kiosk_username)
            if not service_mode_record:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Service mode record not found for kiosk '{kiosk_username}'"
                )
            
            # Get kiosk user
            kiosk_user = kiosk_service_mode_db_crud.get_kiosk_user_by_username(db, kiosk_username)
            if not kiosk_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Kiosk user '{kiosk_username}' not found"
                )
            
            return KioskServiceModeStatus(
                kiosk_username=service_mode_record.kiosk_username,
                is_service_mode=service_mode_record.is_service_mode,
                service_picture_name=service_mode_record.service_picture_name,
                is_kiosk_active=kiosk_user.is_active,
                has_active_sse_connection=await self._check_kiosk_has_active_sse_connection(kiosk_username)
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get service mode status: {str(e)}"
            )
    
    async def _broadcast_service_mode_change_event(
        self, 
        kiosk_username: str, 
        is_service_mode: bool, 
        service_picture_name: str | None
    ) -> None:
        """
        Broadcast service mode change event via SSE
        
        Args:
            kiosk_username: Kiosk username that changed
            is_service_mode: New service mode status
            service_picture_name: Service picture name (if activating)
        """
        try:
            # Create SSE event
            event = KioskServiceModeChangedEvent(
                kiosk_username=kiosk_username,
                is_service_mode=is_service_mode,
                service_picture_name=service_picture_name
            )
            
            # Broadcast to all kiosk subscribers
            # The SSE service will filter to only send to the specific kiosk
            await bus.publish("kiosk_broadcast", event.model_dump(mode='json'))
            
            print(f"📡 Service mode event broadcasted for kiosk '{kiosk_username}': {is_service_mode}")
            
        except Exception as e:
            print(f"❌ Failed to broadcast service mode event for kiosk '{kiosk_username}': {e}")
            # Don't raise exception here - service mode update should succeed even if SSE fails
    
    async def _check_kiosk_has_active_sse_connection(self, kiosk_username: str) -> bool:
        """
        Check if kiosk has an active SSE connection
        
        Args:
            kiosk_username: Kiosk username to check
            
        Returns:
            True if kiosk has active SSE connection, False otherwise
        """
        try:
            # TODO: Implement actual SSE connection checking
            # For now, return False as placeholder
            # In a real implementation, this would check the SSE service
            # to see if the kiosk has an active connection
            return False
            
        except Exception as e:
            print(f"❌ Failed to check SSE connection for kiosk '{kiosk_username}': {e}")
            return False


# Global logic instance
kiosk_service_mode_logic = KioskServiceModeLogic()