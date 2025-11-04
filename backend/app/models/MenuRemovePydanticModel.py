# MenuRemovePydanticModel.py
# Pydantic models for Menu Remove functionality

from pydantic import BaseModel, Field, validator
from typing import Optional


class MenuDeleteRequest(BaseModel):
    """Request model for deleting a menu by ID or name"""
    menu_id: Optional[int] = Field(None, description="ID of the menu to delete", gt=0)
    menu_name: Optional[str] = Field(None, description="Name of the menu to delete", min_length=1)
    
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
                    "menu_id": 15
                },
                {
                    "menu_name": "Breakfast Menu"
                },
                {
                    "menu_id": 15,
                    "menu_name": "Breakfast Menu"
                }
            ]
        }


class MenuDeleteResponse(BaseModel):
    """Response model for menu deletion operations"""
    success: bool = Field(..., description="Whether the deletion operation was successful")
    message: str = Field(..., description="Human-readable message describing the result")
    deleted_menu_id: Optional[int] = Field(None, description="ID of the deleted menu")
    deleted_menu_name: Optional[str] = Field(None, description="Name of the deleted menu")
    items_deleted: Optional[int] = Field(None, description="Number of menu items deleted")
    categories_deleted: Optional[int] = Field(None, description="Number of menu categories deleted")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Menu deleted successfully",
                "deleted_menu_id": 15,
                "deleted_menu_name": "Breakfast Menu",
                "items_deleted": 12,
                "categories_deleted": 3
            }
        }


class MenuDeleteErrorResponse(BaseModel):
    """Error response model for menu deletion operations"""
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
                    "error": "MENU_NOT_FOUND",
                    "message": "Menu with name 'NonExistent Menu' not found",
                    "menu_name": "NonExistent Menu"
                }
            ]
        }