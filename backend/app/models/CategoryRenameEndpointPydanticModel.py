# CategoryRenameEndpointPydanticModel.py
# Pydantic models for Category Rename API endpoint

from pydantic import BaseModel, Field, ConfigDict, validator
from typing import Literal, Optional
from datetime import datetime
from enum import Enum


# NOTE: Day categories are no longer supported. Rename endpoint is food-only.


class RenameCategoryRequest(BaseModel):
    """
    Request model for renaming food categories.

    Optional fields ru_label and en_label are display-only label overrides for the new category.
    If not provided, labels from the current category will be copied.
    """
    current_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Current category name to rename"
    )
    new_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="New category name (must be unique). Omit to update labels only"
    )
    ru_label: Optional[str] = Field(
        None,
        max_length=200,
        description="Optional Russian display label for the new category"
    )
    en_label: Optional[str] = Field(
        None,
        max_length=200,
        description="Optional English display label for the new category"
    )
    # category_type removed: endpoint is food-only

    @validator('new_name')
    def validate_new_name_different(cls, v, values):
        """Ensure new name is different from current name when provided"""
        if v is None:
            return v
        current_name = values.get('current_name')
        if current_name and v == current_name:
            raise ValueError('New name must be different from current name')
        return v

    # Accept and ignore unknown fields like legacy "category_type" to keep backward compatibility
    model_config = ConfigDict(
        extra="ignore",
        json_schema_extra={
            "examples": [
                {
                    "current_name": "Desserts",
                    "new_name": "Sweet Treats",
                    "ru_label": "Сладости",
                    "en_label": "Sweet Treats"
                },
                {
                    "current_name": "Drinks",
                    "new_name": "Beverages"
                }
            ]
        }
    )


class CategoryRenameResponse(BaseModel):
    """Response model for category renaming operation"""
    success: bool = Field(True, description="Operation success status")
    message: str = Field(..., description="Success message")
    old_name: str = Field(..., description="Previous category name")
    new_name: str = Field(..., description="New category name")
    category_type: str = Field("food", description="Deprecated. Always 'food' since day categories were removed")
    items_updated_count: int = Field(..., description="Number of menu items that were updated with new category name")
    ru_label: Optional[str] = Field(None, description="Resulting Russian display label for the new category")
    en_label: Optional[str] = Field(None, description="Resulting English display label for the new category")
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "success": True,
                    "message": "Food category renamed successfully from 'Drinks' to 'Beverages'",
                    "old_name": "Drinks",
                    "new_name": "Beverages",
                    "category_type": "food",
                    "items_updated_count": 12,
                    "ru_label": "Напитки",
                    "en_label": "Beverages"
                }
            ]
        }
    )


class CategoryRenameValidationError(BaseModel):
    """Error response model for validation failures"""
    success: bool = Field(False, description="Operation success status")
    error_type: str = Field(..., description="Type of validation error")
    message: str = Field(..., description="Detailed error message")
    current_name: str = Field(..., description="Category name that was being renamed")
    new_name: str = Field(..., description="New name that was attempted")
    category_type: str = Field("food", description="Deprecated. Always 'food'")
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "success": False,
                    "error_type": "CATEGORY_NOT_FOUND",
                    "message": "Food category 'NonExistent' not found",
                    "current_name": "NonExistent",
                    "new_name": "NewName",
                    "category_type": "food"
                },
                {
                    "success": False,
                    "error_type": "NAME_ALREADY_EXISTS",
                    "message": "Food category 'Beverages' already exists",
                    "current_name": "Drinks",
                    "new_name": "Beverages",
                    "category_type": "food"
                }
            ]
        }
    )