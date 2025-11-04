# MenuImportPydanticModel.py
# Pydantic models for Menu Import CSV functionality

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
import os
import re
from datetime import time


class MenuImportRequest(BaseModel):
    """Request model for importing menu from CSV file"""
    file_path: str = Field(
        ..., 
        description="Full path to the CSV file to import",
        min_length=1
    )
    menu_name: str = Field(
        ..., 
        description="Name for the new menu",
        min_length=1,
        max_length=255
    )
    description: Optional[str] = Field(
        None, 
        description="Optional description for the menu",
        max_length=1000
    )
    
    @validator('file_path')
    def validate_file_path(cls, v):
        """Validate that the file path exists and is a CSV file"""
        if not v or not v.strip():
            raise ValueError("File path cannot be empty")
        
        normalized_path = os.path.normpath(v.strip())
        
        if not normalized_path.lower().endswith('.csv'):
            raise ValueError("File must be a CSV file (.csv extension)")
            
        return normalized_path
    
    @validator('menu_name')
    def validate_menu_name(cls, v):
        """Validate menu name is not empty and contains valid characters"""
        if not v or not v.strip():
            raise ValueError("Menu name cannot be empty")
        
        # Basic validation - no special characters that could cause issues
        if len(v.strip()) < 2:
            raise ValueError("Menu name must be at least 2 characters long")
            
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "file_path": "/tmp/menu_data.csv",
                "menu_name": "Breakfast Menu",
                "description": "Morning menu items available from 6 AM to 11 AM"
            }
        }


class MenuImportValidationError(BaseModel):
    """Individual validation error details"""
    row_number: int = Field(..., description="Row number where error occurred (1-based)")
    column: Optional[str] = Field(None, description="Column name where error occurred")
    error_type: str = Field(..., description="Type of validation error")
    message: str = Field(..., description="Detailed error message")
    value: Optional[str] = Field(None, description="Invalid value that caused the error")

    class Config:
        json_schema_extra = {
            "example": {
                "row_number": 5,
                "column": "ItemID",
                "error_type": "ITEM_NOT_FOUND",
                "message": "Item with ID 999 does not exist or is archived",
                "value": "999"
            }
        }


class MenuImportResponse(BaseModel):
    """Response model for menu import operations"""
    success: bool = Field(..., description="Whether the import operation was successful")
    message: str = Field(..., description="Human-readable message describing the result")
    menu_id: Optional[int] = Field(None, description="ID of the created menu (if successful)")
    menu_name: Optional[str] = Field(None, description="Name of the created menu")
    items_imported: Optional[int] = Field(None, description="Number of items imported")
    categories_imported: Optional[int] = Field(None, description="Number of categories imported")
    validation_errors: Optional[List[MenuImportValidationError]] = Field(
        None, 
        description="List of validation errors (if any)"
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "success": True,
                    "message": "Menu imported successfully",
                    "menu_id": 15,
                    "menu_name": "Breakfast Menu",
                    "items_imported": 12,
                    "categories_imported": 3,
                    "validation_errors": None
                },
                {
                    "success": False,
                    "message": "CSV validation failed",
                    "menu_id": None,
                    "menu_name": None,
                    "items_imported": None,
                    "categories_imported": None,
                    "validation_errors": [
                        {
                            "row_number": 5,
                            "column": "ItemID",
                            "error_type": "ITEM_NOT_FOUND",
                            "message": "Item with ID 999 does not exist or is archived",
                            "value": "999"
                        }
                    ]
                }
            ]
        }


class MenuImportErrorResponse(BaseModel):
    """Error response model for menu import operations"""
    success: bool = Field(False, description="Always false for error responses")
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Detailed error message")
    file_path: Optional[str] = Field(None, description="File path if applicable")
    validation_errors: Optional[List[MenuImportValidationError]] = Field(
        None, 
        description="Detailed validation errors if applicable"
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "success": False,
                    "error": "FILE_NOT_FOUND",
                    "message": "The specified CSV file does not exist",
                    "file_path": "/invalid/path/menu.csv",
                    "validation_errors": None
                },
                {
                    "success": False,
                    "error": "VALIDATION_FAILED",
                    "message": "CSV data validation failed",
                    "file_path": "/tmp/menu.csv",
                    "validation_errors": [
                        {
                            "row_number": 3,
                            "column": "DisplayOrder",
                            "error_type": "INVALID_INTEGER",
                            "message": "DisplayOrder must be an integer",
                            "value": "abc"
                        }
                    ]
                }
            ]
        }


class CsvRowData(BaseModel):
    """Internal model for parsed CSV row data"""
    row_number: int
    what_sort: str
    food_category: str
    item_id: Optional[str]
    name_rus: Optional[str]
    display_order: str
    start_at: str
    end_at: str
    
    class Config:
        # Allow extra fields for flexibility
        extra = "forbid"