# SuperAdminInitLogic.py
# Business logic for SuperAdmin initialization endpoints
# NOTE: This layer manages full transaction: validation → operation → commit/rollback

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from typing import Dict, Any

from ..models.SuperAdminInitPydanticModel import SuperAdminSetupRequest, SetupStatusResponse
from ..models.AuthenticationEndpointsPydanticModel import LoginResponse
from ..services.SuperAdminInitDBCRUD import superadmin_init_db_crud
from ..services.database_init import db_init_service
from ..auth.auth_service import auth_service
from ..auth.password import password_manager


class SuperAdminInitLogic:
    """Business logic for SuperAdmin initialization endpoints"""
    
    async def create_first_superadmin(self, db: Session, setup_request: SuperAdminSetupRequest) -> Dict[str, Any]:
        """
        First-time SuperAdmin creation with race condition protection
        
        Args:
            db: Database session
            setup_request: SuperAdmin setup request data
            
        Returns:
            Login response with access token and user info
            
        Raises:
            HTTPException: If SuperAdmin already exists or creation fails
        """
        try:
            # Initialize database with default roles if needed (idempotent)
            db_init_service.initialize_database(db)
            
            # Get SuperAdmin role
            superadmin_role = superadmin_init_db_crud.get_superadmin_role(db)
            if not superadmin_role:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="SuperAdmin role not found. Database initialization failed."
                )
            
            # Check if username already exists
            existing_user = superadmin_init_db_crud.get_user_by_username(db, setup_request.username)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Username '{setup_request.username}' already exists"
                )
            
            # Hash password
            password_hash = password_manager.hash_password(setup_request.password)
            
            # Create SuperAdmin user
            superadmin = superadmin_init_db_crud.create_superadmin(
                db=db,
                setup_request=setup_request,
                password_hash=password_hash,
                role_name=superadmin_role.name
            )
            
            # This commit will fail if constraint is violated (another superadmin exists)
            try:
                db.commit()
            except IntegrityError as e:
                db.rollback()
                # Check if it's a superadmin constraint violation
                if "unique_superadmin" in str(e).lower() or "role_id" in str(e).lower():
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="SuperAdmin user already exists. Use regular login endpoint."
                    )
                else:
                    # Some other integrity error (username, email, etc.)
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="User creation failed due to data constraint violation"
                    )
            
            # Refresh to get the created user with all fields
            db.refresh(superadmin)
            
            # Update last login timestamp
            auth_service.get_user_by_id(db, superadmin.user_id)
            
            # Generate access token
            token_data = auth_service.create_token_for_user(superadmin)
            
            return token_data
            
        except HTTPException:
            # Re-raise HTTP exceptions as-is
            db.rollback()
            raise
        except ValueError as e:
            # Convert ValueError to HTTP exception
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            # Catch-all for unexpected errors
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create SuperAdmin: {str(e)}"
            )
    
    async def check_setup_status(self, db: Session) -> SetupStatusResponse:
        """
        Check if the system needs initial SuperAdmin setup
        
        Args:
            db: Database session
            
        Returns:
            Setup status response
            
        Raises:
            HTTPException: If setup status check fails
        """
        try:
            # Initialize database with default roles if needed
            db_init_service.initialize_database(db)
            
            # Check if any SuperAdmin exists
            has_superadmin = superadmin_init_db_crud.has_superadmin(db)
            
            return SetupStatusResponse(
                setup_required=not has_superadmin,
                has_superadmin=has_superadmin,
                message="System ready for first-time setup" if not has_superadmin else "System already configured",
                endpoint="/api/v1/setup/superadmin" if not has_superadmin else "/api/v1/auth/login"
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to check setup status: {str(e)}"
            )


# Global logic instance
superadmin_init_logic = SuperAdminInitLogic()