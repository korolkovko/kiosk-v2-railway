# MediaUpdateLogic.py
# Business logic for Media Update functionality
#
# Purpose:
# Validate media update requests and broadcast SSE events to all connected kiosks.
# Validates identifiers against database (items, categories) or allowed values (static media).

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import logging

from ..models.MediaUpdatePydanticModel import MediaUpdateRequest, MediaUpdateResponse
from ..models.SSEEventModels import MediaUpdateEvent
from ..websockets.event_bus import bus
from ..database.models import ItemLive, FoodCategory

logger = logging.getLogger(__name__)

# Allowed values for static media types
ALLOWED_SERVICE_MODE_NAMES = ["menu", "maintenance", "dayoff"]
ALLOWED_SCREENSAVER_NAME = "screensaver"
ALLOWED_ORDER_HANDLING_NAME = "order_handling"
ALLOWED_PROMOTED_NAME = "promoted"


class MediaUpdateLogic:
    """Business logic for media update operations"""

    async def trigger_media_update(
        self,
        db: Session,
        request: MediaUpdateRequest
    ) -> MediaUpdateResponse:
        """
        Validate media update request and broadcast SSE event to all kiosks

        Validation:
        - item: Must exist in items table and not be archived
        - category_open/category_sorry: Must exist in food_categories table
        - category_promoted: Must be exactly "promoted"
        - screensaver: Must be exactly "screensaver"
        - order_handling: Must be exactly "order_handling"
        - service_mode: Must be one of "menu", "maintenance", "dayoff"

        Args:
            db: Database session
            request: Media update request

        Returns:
            MediaUpdateResponse with operation result

        Raises:
            HTTPException: 404 if identifier not found, 400 if validation fails
        """
        try:
            logger.info(
                f"Media update requested: type={request.media_type}, identifier={request.identifier}"
            )

            # Validate identifier based on media type
            await self._validate_identifier(db, request.media_type, request.identifier)

            # Create SSE event
            event = MediaUpdateEvent(
                media_type=request.media_type,
                identifier=request.identifier
            )

            # Get subscriber count before publishing
            subscriber_count = len(bus._subs.get("kiosk_broadcast", ()))

            # Broadcast to all kiosk subscribers
            await bus.publish("kiosk_broadcast", event.model_dump(mode='json'))

            logger.info(
                f"📡 Media update event broadcasted: type={request.media_type}, "
                f"identifier={request.identifier}, kiosks={subscriber_count}"
            )

            return MediaUpdateResponse(
                success=True,
                message=f"Media update triggered for {request.media_type}: {request.identifier}",
                media_type=request.media_type,
                identifier=request.identifier,
                kiosks_notified=subscriber_count
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during media update: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to trigger media update: {str(e)}"
            )

    async def _validate_identifier(
        self,
        db: Session,
        media_type: str,
        identifier: str
    ) -> None:
        """
        Validate identifier based on media type

        Raises:
            HTTPException: If validation fails
        """
        if media_type == "item":
            await self._validate_item(db, identifier)

        elif media_type in ["category_open", "category_sorry"]:
            await self._validate_category(db, identifier)

        elif media_type == "category_promoted":
            if identifier != ALLOWED_PROMOTED_NAME:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid identifier for category_promoted. Must be exactly '{ALLOWED_PROMOTED_NAME}'"
                )

        elif media_type == "screensaver":
            if identifier != ALLOWED_SCREENSAVER_NAME:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid identifier for screensaver. Must be exactly '{ALLOWED_SCREENSAVER_NAME}'"
                )

        elif media_type == "order_handling":
            if identifier != ALLOWED_ORDER_HANDLING_NAME:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid identifier for order_handling. Must be exactly '{ALLOWED_ORDER_HANDLING_NAME}'"
                )

        elif media_type == "service_mode":
            if identifier not in ALLOWED_SERVICE_MODE_NAMES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid identifier for service_mode. Must be one of: {', '.join(ALLOWED_SERVICE_MODE_NAMES)}"
                )

    async def _validate_item(self, db: Session, item_id_str: str) -> None:
        """
        Validate that item exists and is not archived

        Raises:
            HTTPException: If item not found or archived
        """
        try:
            item_id = int(item_id_str)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid item ID: '{item_id_str}'. Must be a number."
            )

        item = db.query(ItemLive).filter(
            ItemLive.item_id == item_id,
            ItemLive.is_archived == False
        ).first()

        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Item with ID {item_id} not found or is archived"
            )

        logger.info(f"✅ Item validated: ID={item_id}, name={item.name_ru}")

    async def _validate_category(self, db: Session, category_name: str) -> None:
        """
        Validate that category exists in food_categories table

        Raises:
            HTTPException: If category not found
        """
        category = db.query(FoodCategory).filter(
            FoodCategory.name == category_name
        ).first()

        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category '{category_name}' not found in food_categories table"
            )

        logger.info(f"✅ Category validated: name={category_name}")


# Create a singleton instance
media_update_logic = MediaUpdateLogic()
