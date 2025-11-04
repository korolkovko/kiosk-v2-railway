# MenuPreparationPydanticModel.py
# Pydantic models for Menu Preparation CSV export functionality

from pydantic import BaseModel, Field, validator
from typing import Optional
import os


class MenuCsvExportRequest(BaseModel):
    """Request model for exporting non-archived live items and categories to CSV"""
    folder_path: str = Field(
        ..., 
        description="Folder path where the CSV file should be saved",
        min_length=1
    )
    
    @validator('folder_path')
    def validate_folder_path(cls, v):
        """Validate that the folder path is not empty and is a valid path format"""
        if not v or not v.strip():
            raise ValueError("Folder path cannot be empty")
        
        # Normalize the path
        normalized_path = os.path.normpath(v.strip())
        
        # Basic validation - ensure it's not just a root or relative path indicator
        if normalized_path in ['/', '.', '..']:
            raise ValueError("Invalid folder path")
            
        return normalized_path

    class Config:
        json_schema_extra = {
            "example": {
                "folder_path": "/tmp/menu_exports"
            }
        }


class MenuCsvExportResponse(BaseModel):
    """Response model for CSV export operations"""
    success: bool = Field(..., description="Whether the export operation was successful")
    message: str = Field(..., description="Human-readable message describing the result")
    file_path: str = Field(..., description="Full path to the generated CSV file")
    filename: str = Field(..., description="Name of the generated CSV file")
    items_count: int = Field(..., description="Number of non-archived items exported")
    categories_count: int = Field(..., description="Number of unique categories exported")
    total_rows: int = Field(..., description="Total number of rows in the CSV file")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "CSV file generated successfully",
                "file_path": "/tmp/menu_exports/LiveitemsNonArchived_20231022_121530.csv",
                "filename": "LiveitemsNonArchived_20231022_121530.csv",
                "items_count": 45,
                "categories_count": 8,
                "total_rows": 53
            }
        }


class MenuCsvExportErrorResponse(BaseModel):
    """Error response model for CSV export operations"""
    success: bool = Field(False, description="Always false for error responses")
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Detailed error message")
    folder_path: Optional[str] = Field(None, description="Folder path if applicable")

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "success": False,
                    "error": "INVALID_PATH",
                    "message": "The specified folder path is invalid or inaccessible",
                    "folder_path": "/invalid/path"
                },
                {
                    "success": False,
                    "error": "PERMISSION_DENIED",
                    "message": "Permission denied: cannot write to the specified folder",
                    "folder_path": "/protected/folder"
                },
                {
                    "success": False,
                    "error": "NO_DATA",
                    "message": "No non-archived items found to export"
                }
            ]
        }