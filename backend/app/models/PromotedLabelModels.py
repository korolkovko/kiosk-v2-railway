# PromotedLabelModels.py
# Pydantic models for Promoted Label feature (single-record configuration)
# NOTE: This is NOT a category. It is only for displaying the name of promoted items.

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class PromotedLabelCreateRequest(BaseModel):
    """
    Request model for creating the Promoted Label record.

    Note:
    - This table is intended to have only one record globally.
    - Primary key 'name' identifies the record (example: "promoted").
    """
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Primary key name (e.g., 'promoted')"
    )
    ru_label: Optional[str] = Field(
        None,
        max_length=200,
        description="Optional Russian display label"
    )
    en_label: Optional[str] = Field(
        None,
        max_length=200,
        description="Optional English display label"
    )

    model_config = ConfigDict(
        extra="ignore",
        json_schema_extra={
            "examples": [
                {
                    "name": "promoted",
                    "ru_label": "Акции",
                    "en_label": "Promoted"
                }
            ]
        }
    )


class PromotedLabelUpdateRequest(BaseModel):
    """
    Request model for editing the Promoted Label record by name.
    """
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Primary key name to update (e.g., 'promoted')"
    )
    ru_label: Optional[str] = Field(
        None,
        max_length=200,
        description="Optional Russian display label"
    )
    en_label: Optional[str] = Field(
        None,
        max_length=200,
        description="Optional English display label"
    )

    model_config = ConfigDict(
        extra="ignore",
        json_schema_extra={
            "examples": [
                {
                    "name": "promoted",
                    "ru_label": "Промо",
                    "en_label": "Promo"
                }
            ]
        }
    )


class PromotedLabelResponse(BaseModel):
    """
    Response model for Promoted Label record.
    """
    name: str = Field(..., description="Primary key (e.g., 'promoted')")
    ru_label: Optional[str] = Field(None, description="Russian display label")
    en_label: Optional[str] = Field(None, description="English display label")
    created_at: datetime = Field(..., description="Creation timestamp")

    model_config = ConfigDict(from_attributes=True)