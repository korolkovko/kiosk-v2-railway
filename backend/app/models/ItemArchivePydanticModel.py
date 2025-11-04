# ItemArchivePydanticModel.py
from pydantic import BaseModel, Field
from typing import Optional


class ItemArchiveStatusRequest(BaseModel):
    """Request model for archiving/unarchiving an item"""
    item_id: int = Field(..., description="ID of the item to archive/unarchive", gt=0)
    is_archived: bool = Field(..., description="True to archive the item, False to unarchive it")

    class Config:
        json_schema_extra = {
            "example": {
                "item_id": 123,
                "is_archived": True
            }
        }


class ItemArchiveStatusResponse(BaseModel):
    """Response model for archive/unarchive operations"""
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Human-readable message describing the result")
    item_id: int = Field(..., description="ID of the item that was processed")
    is_archived: bool = Field(..., description="Current archive status of the item")
    action_performed: str = Field(..., description="Action that was performed: 'archived' or 'unarchived'")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Item successfully archived",
                "item_id": 123,
                "is_archived": True,
                "action_performed": "archived"
            }
        }


class ItemArchiveErrorResponse(BaseModel):
    """Error response model for archive operations"""
    success: bool = Field(False, description="Always false for error responses")
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Detailed error message")
    item_id: Optional[int] = Field(None, description="Item ID if applicable")

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "success": False,
                    "error": "ITEM_NOT_FOUND",
                    "message": "Item with ID 999 not found",
                    "item_id": 999
                },
                {
                    "success": False,
                    "error": "ALREADY_ARCHIVED",
                    "message": "Item with ID 123 is already archived",
                    "item_id": 123
                },
                {
                    "success": False,
                    "error": "ALREADY_ACTIVE",
                    "message": "Item with ID 123 is already active (not archived)",
                    "item_id": 123
                }
            ]
        }