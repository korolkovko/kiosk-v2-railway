# CategoryManagementPydanticModel.py
# Pydantic models for Category Management API endpoints
# Note: ru_label / en_label are optional, display-only fields for categories. They do not affect identity or relations.

from pydantic import BaseModel, Field, ConfigDict
from typing import Literal, Optional
from datetime import datetime
from enum import Enum


# Day categories removed; food-only category management


class CreateCategoryRequest(BaseModel):
    """
    Request model for creating new food categories.
    """
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Category name (must be unique)"
    )
    ru_label: Optional[str] = Field(
        None,
        max_length=200,
        description="Optional Russian display label for category"
    )
    en_label: Optional[str] = Field(
        None,
        max_length=200,
        description="Optional English display label for category"
    )
    
    # Accept and ignore any unknown legacy fields (e.g., category_type)
    model_config = ConfigDict(
        extra="ignore",
        json_schema_extra={
            "examples": [
                { "name": "Desserts", "ru_label": "Десерты", "en_label": "Desserts" },
                { "name": "Drinks", "ru_label": "Напитки", "en_label": "Beverages" }
            ]
        }
    )


class FoodCategoryResponse(BaseModel):
    """Response model for created FoodCategory"""
    name: str = Field(..., description="Category name")
    category_type: Literal["food"] = Field("food", description="Category type")
    ru_label: Optional[str] = Field(None, description="Optional Russian display label")
    en_label: Optional[str] = Field(None, description="Optional English display label")
    created_at: datetime = Field(..., description="Category creation timestamp")
    
    model_config = ConfigDict(from_attributes=True)


# DayCategoryResponse removed: day categories are no longer supported


class CategoryCreationResponse(BaseModel):
    """Unified response model for category creation"""
    success: bool = Field(True, description="Operation success status")
    message: str = Field(..., description="Success message")
    category: dict = Field(..., description="Created category details")
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "success": True,
                    "message": "Food category 'Desserts' created successfully",
                    "category": {
                        "name": "Desserts",
                        "category_type": "food",
                        "created_at": "2025-10-20T14:30:00Z"
                    }
                }
            ]
        }
    )


class DeleteCategoryRequest(BaseModel):
    """Request model for deleting food categories"""
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Category name to delete"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                { "name": "Desserts" }
            ]
        }
    )


class CategoryLabelUpdateRequest(BaseModel):
    """
    Request model for updating category display labels (ru_label/en_label) without renaming.
    Note: Both fields are optional; only provided fields will be updated.
    """
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Category name to update labels for"
    )
    ru_label: Optional[str] = Field(
        None,
        max_length=200,
        description="Optional new Russian display label"
    )
    en_label: Optional[str] = Field(
        None,
        max_length=200,
        description="Optional new English display label"
    )

    model_config = ConfigDict(
        extra="ignore",
        json_schema_extra={
            "examples": [
                { "name": "Desserts", "ru_label": "Десерты" },
                { "name": "Drinks", "en_label": "Beverages" },
                { "name": "Meals", "ru_label": "Горячие блюда", "en_label": "Meals" }
            ]
        }
    )


class CategoryDeletionResponse(BaseModel):
    """Response model for category deletion"""
    success: bool = Field(True, description="Operation success status")
    message: str = Field(..., description="Success or error message")
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "success": True,
                    "message": "Food category 'Desserts' deleted successfully"
                }
            ]
        }
    )