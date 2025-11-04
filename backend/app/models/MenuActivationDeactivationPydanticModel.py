# MenuActivationDeactivationPydanticModel.py
# Pydantic models for Menu Activation/Deactivation functionality

from pydantic import BaseModel, Field, validator
from typing import Optional


class MenuActivationRequest(BaseModel):
    """Request model for activating or deactivating a menu by ID or name"""
    menu_id: Optional[int] = Field(None, description="ID of the menu to activate/deactivate", gt=0)
    menu_name: Optional[str] = Field(None, description="Name of the menu to activate/deactivate", min_length=1)
    is_active: bool = Field(..., description="True to activate the menu, False to deactivate it")
    
    @validator('menu_name')
    def validate_at_least_one_identifier(cls, v, values):
        """Ensure at least one identifier (ID or name) is provided"""
        menu_id = values.get('menu_id')
        
        if not menu_id and not v:
            raise ValueError("Either menu_id or menu_name must be provided")
        return v

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "menu_id": 15,
                    "is_active": True
                },
                {
                    "menu_name": "Breakfast Menu",
                    "is_active": False
                },
                {
                    "menu_id": 15,
                    "menu_name": "Breakfast Menu",
                    "is_active": True
                }
            ]
        }


class MenuActivationResponse(BaseModel):
    """Response model for menu activation/deactivation operations"""
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Human-readable message describing the result")
    menu_id: int = Field(..., description="ID of the affected menu")
    menu_name: str = Field(..., description="Name of the affected menu")
    is_active: bool = Field(..., description="Current active status of the menu")
    action_performed: str = Field(..., description="Action that was performed: 'activated' or 'deactivated'")
    previously_active_menu: Optional[dict] = Field(
        None, 
        description="Information about menu that was deactivated (if any) when activating this menu"
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "success": True,
                    "message": "Menu activated successfully",
                    "menu_id": 15,
                    "menu_name": "Breakfast Menu",
                    "is_active": True,
                    "action_performed": "activated",
                    "previously_active_menu": {
                        "id": 12,
                        "name": "Lunch Menu"
                    }
                },
                {
                    "success": True,
                    "message": "Menu deactivated successfully",
                    "menu_id": 15,
                    "menu_name": "Breakfast Menu",
                    "is_active": False,
                    "action_performed": "deactivated",
                    "previously_active_menu": None
                }
            ]
        }


class MenuActivationErrorResponse(BaseModel):
    """Error response model for menu activation/deactivation operations"""
    success: bool = Field(False, description="Always false for error responses")
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Detailed error message")
    menu_id: Optional[int] = Field(None, description="Menu ID if applicable")
    menu_name: Optional[str] = Field(None, description="Menu name if applicable")

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "success": False,
                    "error": "MENU_NOT_FOUND",
                    "message": "Menu with ID 999 not found",
                    "menu_id": 999
                },
                {
                    "success": False,
                    "error": "ALREADY_ACTIVE",
                    "message": "Menu 'Breakfast Menu' is already active",
                    "menu_name": "Breakfast Menu"
                },
                {
                    "success": False,
                    "error": "ALREADY_INACTIVE",
                    "message": "Menu 'Lunch Menu' is already inactive",
                    "menu_name": "Lunch Menu"
                }
            ]
        }