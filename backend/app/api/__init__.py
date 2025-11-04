# __init__.py
# API module initialization

from fastapi import APIRouter
from .AuthenticationEndpoints import router as auth_router
from .UserManagement import router as users_router
from .SuperAdminInit import router as setup_router
from .ItemLiveAddEndPoint import router as item_live_add_router
from .ItemLiveStockReplenishmentEndPoint import router as item_live_stock_replenishment_router
from .ItemStopListEndPoint import router as item_stop_list_router
from .ItemUpdatePropertiesEndPoint import router as item_update_properties_router
from .GetAllItemLiveEndPoint import router as get_all_item_live_router
from .ItemArchiveEndpoint import router as item_archive_router
from .KIOSKManagement import router as kiosk_router
from .KioskAuthenticationEndpoints import router as kiosk_auth_router
from .KioskAdminMonitoringEndpoints import router as kiosk_admin_router
from .KioskOrderManagement import router as kiosk_order_router
from .KioskAvailableItemsEndpoint import router as kiosk_available_items_router
from .KioskCategoriesEndpoint import router as kiosk_categories_router
from .AllItemsAndCategoriesFromMenuForPreloadEndpoint import router as all_items_and_categories_from_menu_for_preload_router
from .ItemPromotionEndPoint import router as item_promotion_router
from .KioskItemDetailEndpoint import router as kiosk_item_detail_router
from .CategoryManagementEndpoint import router as category_management_router
from .CategoryRenameEndpoint import router as category_rename_router
from .MenuPreparationEndpoint import router as menu_preparation_router
from .MenuImportEndpoint import router as menu_import_router
from .MenuRemoveEndpoint import router as menu_remove_router
from .MenuActivationDeactivationEndpoint import router as menu_activation_deactivation_router
from .events_sse import router as events_sse_router
from .KioskServiceModeEndpoint import router as kiosk_service_mode_router
from .MediaUpdateEndpoint import router as media_update_router
from .PromotedLabelEndpoint import router as promoted_label_router

# Create main API router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(setup_router)  # First-time setup endpoints
api_router.include_router(auth_router)   # Standard authentication endpoints
api_router.include_router(users_router)  # User management endpoints
api_router.include_router(item_live_add_router)  # Item live add endpoints
api_router.include_router(item_live_stock_replenishment_router)  # Stock replenish/remove endpoints
api_router.include_router(item_stop_list_router)  # Stop list endpoints
api_router.include_router(item_update_properties_router)  # Update item properties endpoint
api_router.include_router(get_all_item_live_router)       # Get all live items endpoint
api_router.include_router(item_archive_router)            # Item archive endpoints
api_router.include_router(category_management_router)     # Category management endpoints
api_router.include_router(promoted_label_router)          # Promoted label endpoints (create/edit) under Category Management
api_router.include_router(category_rename_router)         # Category rename endpoints
api_router.include_router(menu_preparation_router)        # Menu preparation endpoints
api_router.include_router(menu_import_router)             # Menu import endpoints
api_router.include_router(menu_remove_router)             # Menu remove endpoints
api_router.include_router(menu_activation_deactivation_router)  # Menu activation/deactivation endpoints
api_router.include_router(kiosk_router)                   # Kiosk management endpoints
api_router.include_router(kiosk_auth_router)              # Kiosk authentication endpoints
api_router.include_router(kiosk_admin_router)             # Kiosk admin monitoring endpoints
api_router.include_router(kiosk_order_router)             # Kiosk order management endpoints
api_router.include_router(kiosk_available_items_router)   # Kiosk available items endpoint
api_router.include_router(kiosk_categories_router)        # Kiosk categories endpoint
api_router.include_router(all_items_and_categories_from_menu_for_preload_router)  # Kiosk menu items for preload
api_router.include_router(item_promotion_router)          # Item promotion toggle endpoint
api_router.include_router(kiosk_item_detail_router)       # Kiosk item detail endpoint
api_router.include_router(kiosk_service_mode_router)      # Kiosk service mode management endpoints
api_router.include_router(media_update_router)            # Media update endpoints
api_router.include_router(events_sse_router)              # SSE events endpoint

__all__ = ["api_router"]