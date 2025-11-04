# Menu-Based Architecture Transition Plan

**Document Created:** 2025-10-22
**Purpose:** Transition from direct item/category fetching to menu-based kiosk interaction

---

## Executive Summary

This document provides a comprehensive analysis and implementation plan for transitioning the kiosk application from fetching all available items/categories to a menu-based filtered approach. The transition will preserve all existing SSE real-time update functionality while adding menu-based filtering, display ordering, and time-based visibility control.

---

## Table of Contents

1. [Current Architecture Analysis](#1-current-architecture-analysis)
2. [Target Architecture Requirements](#2-target-architecture-requirements)
3. [What We Already Have](#3-what-we-already-have)
4. [Changes Required](#4-changes-required)
5. [Implementation Plan](#5-implementation-plan)
6. [Database Query Changes](#6-database-query-changes)
7. [Edge Cases & Solutions](#7-edge-cases--solutions)
8. [Testing Strategy](#8-testing-strategy)
9. [Performance Considerations](#9-performance-considerations)

---

## 1. Current Architecture Analysis

### 1.1 Existing Database Tables

#### Core Item Tables
- `items_live` - Active menu items
- `items_live_available` - Stock availability tracking
- `food_categories` - Category definitions

#### NEW Menu Tables (Already Created)
- `menus` - Menu configuration (id, name, description, is_active)
- `menu_categories` - Categories included in menu with display_order
- `menu_items` - Items in menu with display_order, start_at, end_at

### 1.2 Current Kiosk Data Flow

```
┌─────────────┐
│   LOGIN     │
└──────┬──────┘
       │
       ├──► GET /api/kiosk/items/available
       │    Returns: ALL active items with stock > 0
       │    No menu filtering
       │
       ├──► GET /api/kiosk/categories
       │    Returns: ALL food categories
       │    No menu filtering
       │
       └──► SSE /api/kiosk/events
            Real-time updates for ALL items
            7 event types
```

### 1.3 Current Backend Files & Logic

**Items Endpoint:**
- **File:** `backend/app/api/KioskAvailableItemsEndpoint.py`
- **Endpoint:** `GET /api/kiosk/items/available`
- **Logic Chain:**
  1. `KioskAvailableItemsEndpoint.get_available_items_for_kiosk()`
  2. → `GetAvailableItemsForKioskLogic.get_available_items_for_kiosk()`
  3. → `GetAvailableItemsForKioskDBCRUD.get_available_items_for_kiosk()`
     - Query: `ItemLive` JOIN `ItemLiveAvailable`
     - Filters: `is_active=True`, `is_archived=False`, `stock_quantity>0`
     - Returns: List of all matching items

**Categories Endpoint:**
- **File:** `backend/app/api/KioskCategoriesEndpoint.py`
- **Endpoint:** `GET /api/kiosk/categories`
- **Logic:** Returns ALL food categories without filtering

**Current Response Structure:**
```python
class KioskAvailableItemResponse:
    item_id: int
    name_ru: str
    name_eng: Optional[str]
    description_ru: str
    description_eng: Optional[str]
    unit_measure_name_eng: str
    food_category_name: str
    price_net_kopecks: int          # Integer kopecks
    vat_rate: Optional[Decimal]
    vat_amount_kopecks: int
    price_gross_kopecks: int
    is_active: bool
    promoted: bool
    stock_quantity: int
    # NO display_order fields
    # NO time filtering
```

### 1.4 Existing SSE Events (7 Types)

**File:** `backend/app/models/SSEEventModels.py`
**Service:** `backend/app/services/ItemEventService.py`

| Event Type | Purpose | Fields |
|------------|---------|--------|
| `ITEM_STATUS_CHANGED` | Stop list on/off | item_id, is_active |
| `ITEM_PROMOTION_CHANGED` | Promoted flag | item_id, promoted |
| `ITEM_STOCK_CHANGED` | Stock updates | item_id, stock_quantity, change_quantity |
| `ITEM_CREATED` | New item added | Full item details in kopecks |
| `ITEM_PROPERTIES_CHANGED` | Name/price/description updates | Full item details in kopecks |
| `ORDER_STATUS_CHANGED` | Order status updates | order_id, status |
| `ORDER_EVENT_TRIGGERED` | FSM state changes | order_id, fsm_event, fsm_state |

**Broadcast Channel:** `"kiosk_broadcast"` (all connected kiosks receive all events)

### 1.5 Frontend Data Flow

**Hook:** `useGetAvailableItems()` in `frontend/apps/kiosk/src/hooks/useGetAvailableItems.ts`

**Data Transformation Pipeline:**
```
Backend (kopecks) → HTTP Response (DTO)
                    ↓
                API Layer (.api.ts)
                    ↓
            Service Layer (.service.ts)
                    ↓
        mapGetAvailableItemsDtoToDomain()  ← Kopecks to Rubles
                    ↓
            Domain Model (business logic)
                    ↓
        mapGetAvailableItemsDomainToVM()   ← Format for display
                    ↓
            View Model (UI ready)
```

**SSE Connection:**
- **Service:** `frontend/apps/kiosk/src/SSESubscription/sseService.ts`
- **Hook:** `frontend/apps/kiosk/src/SSESubscription/useSSEItemUpdates.ts`
- **Connection:** EventSource to `/api/kiosk/events?token=<JWT>`
- **Auto-reconnect:** Max 10 attempts, exponential backoff (up to 30s)
- **Heartbeat:** 15 seconds

### 1.6 Existing Menu Management

**Files:**
- `backend/app/services/MenuActivationDeactivationDBCRUD.py`
- `backend/app/logic/MenuActivationDeactivationLogic.py`
- `backend/app/api/MenuActivationDeactivationEndpoint.py`

**Key Functions:**
- `get_currently_active_menu(db)` - Returns active menu or None
- `activate_menu(db, menu)` - Activates a menu (only 1 active at a time)
- `deactivate_menu(db, menu)` - Deactivates a menu

**Business Rule:** Only ONE menu can be active at a time

---

## 2. Target Architecture Requirements

### 2.1 Functional Requirements

1. **Menu Filtering**
   - Kiosk must only receive items that are in the active menu
   - Kiosk must only receive categories that are in the active menu
   - If no active menu exists, kiosk shows error message (stays on login page)

2. **Display Order**
   - Items must be ordered by `menu_items.display_order` within each category
   - Categories must be ordered by `menu_categories.display_order`
   - Frontend must respect this ordering in UI

3. **Time-Based Visibility**
   - Items with `start_at` and `end_at` only display within that time window
   - Items without time restrictions display all day
   - Time comparison uses current server time

4. **Preserve Existing Functionality**
   - All SSE events continue to work
   - Stock updates work as before
   - Stop list functionality preserved
   - Price/property updates preserved
   - No breaking changes to existing endpoints

5. **Error Handling**
   - No active menu → Show clear error message
   - Don't proceed past login page if no menu
   - Provide admin contact information

### 2.2 Non-Functional Requirements

- **Performance:** Query time increase < 10ms with proper indexes
- **Backward Compatibility:** Old clients (if any) should not break
- **Logging:** Log menu filtering decisions for debugging
- **Maintainability:** Reuse existing code where possible

---

## 3. What We Already Have

### ✅ No Changes Needed

1. **Menu Tables** - Already created with proper schema
   - `menus` (id, name, description, is_active)
   - `menu_categories` (id, menu_id, food_category_name, display_order, is_visible)
   - `menu_items` (id, menu_id, item_id, food_category_name, display_order, start_at, end_at)

2. **Menu Management Logic** - Already implemented
   - Activate/deactivate menus
   - Only 1 active menu at a time
   - Admin endpoints for menu management

3. **SSE Infrastructure** - No changes needed
   - Event publishing works
   - All 7 event types defined
   - Broadcast to all kiosks

4. **Frontend State Management** - Compatible
   - `useGetAvailableItems` hook can handle new fields
   - SSE event handlers are flexible
   - Sorting logic can be added

5. **Database Indexes** - Already exist
   - `ix_menu_items_menu_id` on menu_items(menu_id)
   - `ix_menu_categories_menu_id` on menu_categories(menu_id)
   - Composite indexes for query performance

---

## 4. Changes Required

### 4.1 Backend Changes

#### Change 1: Modify GetAvailableItemsForKioskDBCRUD (CRITICAL)

**File:** `backend/app/services/GetAvailableItemsForKioskDBCRUD.py`

**Current Implementation:**
```python
def get_available_items_for_kiosk(self, db: Session) -> List[ItemLive]:
    return (
        db.query(ItemLive)
        .join(ItemLiveAvailable)
        .filter(ItemLive.is_active == True)
        .filter(ItemLive.is_archived == False)
        .filter(ItemLiveAvailable.stock_quantity > 0)
        .options(joinedload(ItemLive.availability))
        .all()
    )
```

**New Implementation (Menu-Filtered):**
```python
from sqlalchemy import func, or_
from datetime import datetime
from ..database.models import Menu, MenuItem, MenuCategory

def get_available_items_for_kiosk(self, db: Session) -> List[tuple]:
    """
    Get available items filtered by active menu with display order.

    Returns:
        List of tuples: (ItemLive, display_order, category_display_order, start_at, end_at)
    """
    # Get active menu
    active_menu = db.query(Menu).filter(Menu.is_active == True).first()

    if not active_menu:
        return []  # No active menu = no items

    current_time = datetime.now().time()

    # Query items through menu_items junction table
    return (
        db.query(
            ItemLive,
            MenuItem.display_order,
            MenuCategory.display_order.label('category_display_order'),
            MenuItem.start_at,
            MenuItem.end_at
        )
        .join(ItemLiveAvailable, ItemLive.item_id == ItemLiveAvailable.item_id)
        .join(MenuItem, MenuItem.item_id == ItemLive.item_id)
        .join(
            MenuCategory,
            (MenuCategory.food_category_name == ItemLive.food_category_name) &
            (MenuCategory.menu_id == MenuItem.menu_id)
        )
        .filter(MenuItem.menu_id == active_menu.id)
        .filter(MenuCategory.is_visible == True)
        .filter(ItemLive.is_active == True)
        .filter(ItemLive.is_archived == False)
        .filter(ItemLiveAvailable.stock_quantity > 0)
        # Time filtering
        .filter(
            or_(
                MenuItem.start_at.is_(None),
                MenuItem.start_at <= current_time
            )
        )
        .filter(
            or_(
                MenuItem.end_at.is_(None),
                MenuItem.end_at >= current_time
            )
        )
        .options(joinedload(ItemLive.availability))
        .order_by(MenuCategory.display_order, MenuItem.display_order)
        .all()
    )
```

**Key Changes:**
- ✅ Added Menu table query to get active menu
- ✅ Joined MenuItem table for menu filtering
- ✅ Joined MenuCategory table for category display order
- ✅ Added time-based filtering (start_at/end_at)
- ✅ Returns tuples with display order data
- ✅ Returns empty list if no active menu
- ✅ Preserves all existing filters

---

#### Change 2: Update Response Model (CRITICAL)

**File:** `backend/app/models/KioskAvailableItemsResponseModel.py`

**Add New Fields:**
```python
from datetime import time
from typing import Optional

class KioskAvailableItemResponse(BaseModel):
    # Existing fields
    item_id: int
    name_ru: str
    name_eng: Optional[str]
    description_ru: str
    description_eng: Optional[str]
    unit_measure_name_eng: str
    food_category_name: str
    price_net_kopecks: int
    vat_rate: Optional[Decimal]
    vat_amount_kopecks: int
    price_gross_kopecks: int
    is_active: bool
    promoted: bool
    stock_quantity: int

    # NEW FIELDS FOR MENU
    display_order: int = Field(..., description="Display order within category")
    category_display_order: int = Field(..., description="Category display order")
    start_at: Optional[time] = Field(None, description="Time when item starts displaying")
    end_at: Optional[time] = Field(None, description="Time when item stops displaying")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                # ... existing example ...
                "display_order": 1,
                "category_display_order": 2,
                "start_at": "06:00:00",
                "end_at": "11:00:00"
            }
        }
    )
```

---

#### Change 3: Update Logic Layer (CRITICAL)

**File:** `backend/app/logic/GetAvailableItemsForKioskLogic.py`

**Update to handle tuple response:**
```python
async def get_available_items_for_kiosk(self, db: Session) -> List[KioskAvailableItemResponse]:
    """Get available items for kiosk with menu filtering"""

    # Get items with display order from CRUD
    items_with_order = get_available_items_for_kiosk_db_crud.get_available_items_for_kiosk(db)

    # Transform to response models
    response = []
    for item, display_order, category_display_order, start_at, end_at in items_with_order:
        response.append(KioskAvailableItemResponse(
            item_id=item.item_id,
            name_ru=item.name_ru,
            name_eng=item.name_eng,
            description_ru=item.description_ru,
            description_eng=item.description_eng,
            unit_measure_name_eng=item.unit_measure_name_eng,
            food_category_name=item.food_category_name,
            price_net_kopecks=item.price_net_kopecks,
            vat_rate=item.vat_rate,
            vat_amount_kopecks=item.vat_amount_kopecks,
            price_gross_kopecks=item.price_gross_kopecks,
            is_active=item.is_active,
            promoted=item.promoted,
            stock_quantity=item.availability.stock_quantity,
            # NEW FIELDS
            display_order=display_order,
            category_display_order=category_display_order,
            start_at=start_at,
            end_at=end_at
        ))

    return response
```

---

#### Change 4: Modify Categories Endpoint (HIGH PRIORITY)

**File:** `backend/app/services/KioskCategoriesDBCRUD.py`

**Current:**
```python
def get_all_food_categories(self, db: Session) -> List[FoodCategory]:
    return db.query(FoodCategory).all()
```

**New (Menu-Filtered):**
```python
from ..database.models import Menu, MenuCategory, FoodCategory

def get_all_food_categories(self, db: Session) -> List[tuple]:
    """
    Get categories filtered by active menu with display order.

    Returns:
        List of tuples: (FoodCategory, display_order)
    """
    # Get active menu
    active_menu = db.query(Menu).filter(Menu.is_active == True).first()

    if not active_menu:
        return []  # No active menu = no categories

    return (
        db.query(FoodCategory, MenuCategory.display_order)
        .join(
            MenuCategory,
            MenuCategory.food_category_name == FoodCategory.name
        )
        .filter(MenuCategory.menu_id == active_menu.id)
        .filter(MenuCategory.is_visible == True)
        .order_by(MenuCategory.display_order)
        .all()
    )
```

**Update Response Model:**
```python
# File: backend/app/models/KioskCategoriesPydanticModel.py

class KioskCategoryResponse(BaseModel):
    name: str
    created_at: datetime
    display_order: int  # NEW FIELD
```

**Update Logic:**
```python
# File: backend/app/logic/KioskCategoriesLogic.py

async def get_all_categories_for_kiosk(self, db: Session) -> KioskCategoriesListResponse:
    categories_with_order = kiosk_categories_db_crud.get_all_food_categories(db)

    categories = [
        KioskCategoryResponse(
            name=cat.name,
            created_at=cat.created_at,
            display_order=display_order
        )
        for cat, display_order in categories_with_order
    ]

    return KioskCategoriesListResponse(
        categories=categories,
        total_count=len(categories)
    )
```

---

#### Change 5: Create Active Menu Check Endpoint (HIGH PRIORITY)

**File:** `backend/app/api/KioskActiveMenuEndpoint.py` (NEW FILE)

```python
# KioskActiveMenuEndpoint.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..auth import get_current_kiosk_user
from ..services.MenuActivationDeactivationDBCRUD import menu_activation_deactivation_db_crud
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/kiosk/menu", tags=["kiosk-menu"])

class MenuInfo(BaseModel):
    id: int
    name: str
    description: Optional[str]

class ActiveMenuResponse(BaseModel):
    has_active_menu: bool
    menu: Optional[MenuInfo] = None

@router.get("/active", response_model=ActiveMenuResponse)
async def get_active_menu(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_kiosk_user)
):
    """
    Check if there is an active menu available for the kiosk.

    Returns:
        Active menu information or indication that no menu is active
    """
    active_menu = menu_activation_deactivation_db_crud.get_currently_active_menu(db)

    if not active_menu:
        return ActiveMenuResponse(
            has_active_menu=False,
            menu=None
        )

    return ActiveMenuResponse(
        has_active_menu=True,
        menu=MenuInfo(
            id=active_menu.id,
            name=active_menu.name,
            description=active_menu.description
        )
    )
```

**Register in main.py:**
```python
# backend/app/main.py
from app.api import KioskActiveMenuEndpoint

app.include_router(
    KioskActiveMenuEndpoint.router,
    prefix="/api/v1"
)
```

---

#### Change 6: Update Existing Single Item Endpoint (MEDIUM PRIORITY)

**✅ ENDPOINT ALREADY EXISTS:** `GET /api/kiosk/items/{item_id}`
- **File:** `backend/app/api/KioskItemDetailEndpoint.py`
- **CRUD:** `backend/app/services/KioskItemDetailDBCRUD.py`
- **Logic:** `backend/app/logic/KioskItemDetailLogic.py`

**Current Implementation:**
```python
# KioskItemDetailDBCRUD.py - EXISTING
def get_item_by_id(self, db: Session, item_id: int) -> Optional[ItemLive]:
    """Get item by ID with stock > 0, active, not archived"""
    return (
        db.query(ItemLive)
        .join(ItemLiveAvailable)
        .filter(ItemLive.item_id == item_id)
        .filter(ItemLive.is_active == True)
        .filter(ItemLive.is_archived == False)
        .filter(ItemLiveAvailable.stock_quantity > 0)
        .options(joinedload(ItemLive.availability))
        .first()
    )
```

**What Needs to Change:**
Add menu filtering to the existing method:

```python
# KioskItemDetailDBCRUD.py - UPDATED
from ..database.models import Menu, MenuItem, MenuCategory

def get_item_by_id(self, db: Session, item_id: int) -> Optional[tuple]:
    """
    Get item by ID if it's in the active menu.
    Returns tuple: (ItemLive, display_order, category_display_order, start_at, end_at)
    """
    # Get active menu
    active_menu = db.query(Menu).filter(Menu.is_active == True).first()

    if not active_menu:
        return None

    current_time = datetime.now().time()

    return (
        db.query(
            ItemLive,
            MenuItem.display_order,
            MenuCategory.display_order.label('category_display_order'),
            MenuItem.start_at,
            MenuItem.end_at
        )
        .join(ItemLiveAvailable, ItemLive.item_id == ItemLiveAvailable.item_id)
        .join(MenuItem, MenuItem.item_id == ItemLive.item_id)
        .join(
            MenuCategory,
            (MenuCategory.food_category_name == ItemLive.food_category_name) &
            (MenuCategory.menu_id == MenuItem.menu_id)
        )
        .filter(MenuItem.menu_id == active_menu.id)
        .filter(ItemLive.item_id == item_id)
        .filter(MenuCategory.is_visible == True)
        .filter(ItemLive.is_active == True)
        .filter(ItemLive.is_archived == False)
        .filter(ItemLiveAvailable.stock_quantity > 0)
        .filter(
            or_(
                MenuItem.start_at.is_(None),
                MenuItem.start_at <= current_time
            )
        )
        .filter(
            or_(
                MenuItem.end_at.is_(None),
                MenuItem.end_at >= current_time
            )
        )
        .options(joinedload(ItemLive.availability))
        .first()
    )
```

**Update Logic Layer:**
```python
# KioskItemDetailLogic.py - UPDATED
async def get_kiosk_item_detail(
    self, db: Session, item_id: int, current_user
) -> KioskAvailableItemResponse:
    result = kiosk_item_detail_db_crud.get_item_by_id(db, item_id)

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Item not found in active menu or not available"
        )

    # Unpack tuple
    item, display_order, category_display_order, start_at, end_at = result

    return KioskAvailableItemResponse(
        item_id=item.item_id,
        name_ru=item.name_ru,
        # ... all existing fields ...
        display_order=display_order,
        category_display_order=category_display_order,
        start_at=start_at,
        end_at=end_at
    )
```

**No endpoint changes needed** - existing endpoint will work with updated logic

---

#### Change 7: SSE Events (NO CHANGES)

**Decision:** Keep SSE events unchanged

**Rationale:**
- Events already broadcast to all kiosks
- Frontend can filter events client-side
- Simpler than per-kiosk filtering
- Lower server complexity
- Frontend already handles gracefully

**How it works:**
1. Item stock update SSE arrives at kiosk
2. Frontend checks if item exists in current item list
3. If exists → Update
4. If not exists → Call GET /api/kiosk/items/{item_id} to check if in menu
5. If in menu → Add to list
6. If not in menu → Ignore

---

### 4.2 Frontend Changes

#### Change 1: Create useActiveMenu Hook (HIGH PRIORITY)

**File:** `frontend/apps/kiosk/src/hooks/useActiveMenu.ts` (NEW FILE)

```typescript
import { useState, useEffect } from 'react'
import { getAccessToken } from '../auth/tokenStorage'

interface MenuInfo {
  id: number
  name: string
  description: string | null
}

interface ActiveMenuResponse {
  has_active_menu: boolean
  menu: MenuInfo | null
}

interface UseActiveMenuResult {
  hasActiveMenu: boolean
  menuInfo: MenuInfo | null
  loading: boolean
  error: Error | null
  refetch: () => Promise<void>
}

export const useActiveMenu = (): UseActiveMenuResult => {
  const [hasActiveMenu, setHasActiveMenu] = useState<boolean>(false)
  const [menuInfo, setMenuInfo] = useState<MenuInfo | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<Error | null>(null)

  const fetchActiveMenu = async () => {
    setLoading(true)
    setError(null)

    try {
      const token = getAccessToken()
      const response = await fetch('/api/kiosk/menu/active', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (!response.ok) {
        throw new Error('Failed to fetch active menu')
      }

      const data: ActiveMenuResponse = await response.json()

      setHasActiveMenu(data.has_active_menu)
      setMenuInfo(data.menu)
    } catch (err) {
      setError(err as Error)
      setHasActiveMenu(false)
      setMenuInfo(null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchActiveMenu()
  }, [])

  return {
    hasActiveMenu,
    menuInfo,
    loading,
    error,
    refetch: fetchActiveMenu
  }
}
```

---

#### Change 2: Update Data Models (HIGH PRIORITY)

**File 1:** `frontend/apps/kiosk/src/models/dto/getAvailableItems.dto.ts`

```typescript
export interface GetAvailableItemDto {
  // Existing fields
  item_id: number
  name_ru: string
  name_eng: string | null
  description_ru: string
  description_eng: string | null
  unit_measure_name_eng: string
  food_category_name: string
  price_net_kopecks: number
  vat_rate: string | null
  vat_amount_kopecks: number
  price_gross_kopecks: number
  is_active: boolean
  promoted: boolean
  stock_quantity: number

  // NEW MENU FIELDS
  display_order: number
  category_display_order: number
  start_at: string | null          // ISO time string "HH:MM:SS"
  end_at: string | null            // ISO time string "HH:MM:SS"
}
```

**File 2:** `frontend/apps/kiosk/src/models/domain/availableItem.ts`

```typescript
export interface AvailableItem {
  // Existing fields
  itemId: number
  nameRu: string
  nameEng: string | null
  descriptionRu: string
  descriptionEng: string | null
  unitMeasure: string
  foodCategory: string
  priceNet: number               // Decimal rubles
  vatRate: number | null
  vatAmount: number
  priceGross: number
  isActive: boolean
  promoted: boolean
  stockQuantity: number

  // NEW MENU FIELDS
  displayOrder: number
  categoryDisplayOrder: number
  startAt: string | null
  endAt: string | null
}
```

**File 3:** `frontend/apps/kiosk/src/models/view/availableItem.vm.ts`

```typescript
export interface AvailableItemVM {
  // Existing fields
  itemId: number
  nameRu: string
  nameEng: string | null
  descriptionRu: string
  descriptionEng: string | null
  unitMeasure: string
  foodCategory: string
  priceGrossDisplay: string      // "150.00 ₽"
  priceNetDisplay: string
  vatRateDisplay: string | null
  priceGross: number
  priceNet: number
  vatRate: number | null
  promoted: boolean
  stockQuantity: number
  isAvailable: boolean
  posterPath: string

  // NEW MENU FIELDS
  displayOrder: number
  categoryDisplayOrder: number
}
```

---

#### Change 3: Update Mappers (HIGH PRIORITY)

**File:** `frontend/apps/kiosk/src/services/mappers/getAvailableItems.mappers.ts`

**Update DTO → Domain mapper:**
```typescript
export const mapGetAvailableItemsDtoToDomain = (
  dto: GetAvailableItemDto
): AvailableItem => {
  return {
    // Existing mappings
    itemId: dto.item_id,
    nameRu: dto.name_ru,
    nameEng: dto.name_eng,
    // ... all existing fields ...

    // NEW MENU FIELD MAPPINGS
    displayOrder: dto.display_order,
    categoryDisplayOrder: dto.category_display_order,
    startAt: dto.start_at,
    endAt: dto.end_at
  }
}
```

**Update Domain → VM mapper:**
```typescript
export const mapGetAvailableItemsDomainToVM = (
  domain: AvailableItem
): AvailableItemVM => {
  return {
    // Existing mappings
    itemId: domain.itemId,
    nameRu: domain.nameRu,
    // ... all existing fields ...

    // NEW MENU FIELD MAPPINGS
    displayOrder: domain.displayOrder,
    categoryDisplayOrder: domain.categoryDisplayOrder
    // Note: start_at/end_at not needed in VM (backend filters by time)
  }
}
```

---

#### Change 4: Implement Display Order Sorting (HIGH PRIORITY)

**File:** `frontend/apps/kiosk/src/hooks/useGetAvailableItems.ts`

**Add sorting logic:**
```typescript
export const useGetAvailableItems = () => {
  const [items, setItems] = useState<AvailableItemVM[]>([])
  // ... existing state ...

  // Sort items by display order
  const sortedItems = useMemo(() => {
    return [...items].sort((a, b) => {
      // First sort by category display order
      if (a.categoryDisplayOrder !== b.categoryDisplayOrder) {
        return a.categoryDisplayOrder - b.categoryDisplayOrder
      }
      // Then by item display order within category
      return a.displayOrder - b.displayOrder
    })
  }, [items])

  // Return sorted items instead of unsorted
  return {
    items: sortedItems,  // Changed from items to sortedItems
    loading,
    error,
    refetch,
    connectionStatus
  }
}
```

---

#### Change 5: Add "No Menu" Error Screen (HIGH PRIORITY)

**File:** `frontend/apps/kiosk/src/components/NoMenuAvailable.tsx` (NEW FILE)

```typescript
import React from 'react'
import { useNavigate } from 'react-router-dom'

interface NoMenuAvailableProps {
  onLogout?: () => void
}

export const NoMenuAvailable: React.FC<NoMenuAvailableProps> = ({ onLogout }) => {
  const navigate = useNavigate()

  const handleBackToLogin = () => {
    if (onLogout) {
      onLogout()
    }
    navigate('/login')
  }

  return (
    <div className="no-menu-screen">
      <div className="no-menu-content">
        <div className="icon-container">
          <svg className="menu-off-icon" viewBox="0 0 24 24">
            {/* Menu off icon */}
            <path d="M3 6h18v2H3V6zm0 5h18v2H3v-2zm0 5h18v2H3v-2z" />
            <path d="M2 2l20 20" stroke="currentColor" strokeWidth="2" />
          </svg>
        </div>

        <h1 className="title">No Menu Available</h1>

        <p className="message">
          There is currently no active menu configured for this kiosk.
          Please contact your system administrator.
        </p>

        <button
          className="back-button"
          onClick={handleBackToLogin}
        >
          Back to Login
        </button>
      </div>
    </div>
  )
}
```

---

#### Change 6: Integrate Active Menu Check in App (CRITICAL)

**File:** `frontend/apps/kiosk/src/App.tsx` or main kiosk component

```typescript
import { useActiveMenu } from './hooks/useActiveMenu'
import { NoMenuAvailable } from './components/NoMenuAvailable'
import { useGetAvailableItems } from './hooks/useGetAvailableItems'

export const KioskApp = () => {
  const { hasActiveMenu, menuInfo, loading: menuLoading } = useActiveMenu()
  const { items, loading: itemsLoading } = useGetAvailableItems()

  // Show loading while checking for menu
  if (menuLoading) {
    return <LoadingSpinner message="Checking menu availability..." />
  }

  // Show error if no active menu
  if (!hasActiveMenu) {
    return <NoMenuAvailable onLogout={handleLogout} />
  }

  // Show menu name in header (optional)
  return (
    <div className="kiosk-app">
      <header>
        <h1>{menuInfo?.name || 'Menu'}</h1>
      </header>

      {itemsLoading ? (
        <LoadingSpinner message="Loading items..." />
      ) : (
        <ItemsList items={items} />
      )}
    </div>
  )
}
```

---

#### Change 7: SSE Event Handling (NO MAJOR CHANGES)

**File:** `frontend/apps/kiosk/src/hooks/useGetAvailableItems.ts`

**Current handleItemUpdate logic works as-is:**
- If item in list → Update
- If item not in list → Optionally fetch from GET /api/kiosk/items/{item_id}
- Backend will return 404 if item not in active menu

**Optional enhancement:**
```typescript
const handleItemUpdate = async (updateData: ItemUpdateData) => {
  const existingItemIndex = items.findIndex(
    item => item.itemId === updateData.itemId
  )

  if (existingItemIndex >= 0) {
    // Item exists, update it
    const updatedItems = [...items]
    updatedItems[existingItemIndex] = {
      ...updatedItems[existingItemIndex],
      ...updateData
    }
    setItems(updatedItems)
  } else if (updateData.stockQuantity && updateData.stockQuantity > 0) {
    // Item not in list but has stock - check if it's in menu
    try {
      const response = await fetch(`/api/kiosk/items/${updateData.itemId}`, {
        headers: { Authorization: `Bearer ${getAccessToken()}` }
      })

      if (response.ok) {
        const itemData = await response.json()
        const newItem = mapToViewModel(itemData)
        setItems(prev => [...prev, newItem])
      }
      // If 404, item not in menu - ignore
    } catch (err) {
      console.error('Failed to fetch item:', err)
    }
  }
}
```

---

## 5. Implementation Plan

### Phase 1: Backend Core (Days 1-2)

**Priority: CRITICAL - Must complete before frontend**

#### Day 1 Morning
- [ ] **Task 1.1:** Update `GetAvailableItemsForKioskDBCRUD.py`
  - Implement menu filtering query
  - Add time filtering logic
  - Return tuple with display orders
  - **Test:** Write unit test for query
  - **Estimate:** 2 hours

- [ ] **Task 1.2:** Update `KioskAvailableItemsResponseModel.py`
  - Add 4 new fields (display_order, category_display_order, start_at, end_at)
  - Update Pydantic model
  - Update example in schema
  - **Test:** Validate serialization
  - **Estimate:** 30 minutes

#### Day 1 Afternoon
- [ ] **Task 1.3:** Update `GetAvailableItemsForKioskLogic.py`
  - Handle tuple unpacking
  - Map to response model
  - **Test:** Integration test with mock DB
  - **Estimate:** 1 hour

- [ ] **Task 1.4:** Update Categories CRUD
  - Modify `KioskCategoriesDBCRUD.py`
  - Add menu filtering
  - Return display_order
  - **Test:** Unit test
  - **Estimate:** 1 hour

- [ ] **Task 1.5:** Update Categories Logic & Response
  - Modify `KioskCategoriesLogic.py`
  - Update `KioskCategoriesPydanticModel.py`
  - **Test:** Integration test
  - **Estimate:** 1 hour

#### Day 2 Morning
- [ ] **Task 1.6:** Create Active Menu Endpoint
  - Create `KioskActiveMenuEndpoint.py`
  - Implement GET /api/kiosk/menu/active
  - Register in main.py
  - **Test:** Postman/curl test
  - **Estimate:** 1 hour

- [ ] **Task 1.7:** Update Existing Single Item Endpoint
  - ✅ Endpoint already exists: `GET /api/kiosk/items/{item_id}`
  - Update `KioskItemDetailDBCRUD.get_item_by_id()` to add menu filtering
  - Update `KioskItemDetailLogic` to handle tuple response
  - **Test:** Postman test with menu filtering
  - **Estimate:** 1 hour

#### Day 2 Afternoon
- [ ] **Task 1.8:** Backend Testing
  - Test with no active menu (returns empty)
  - Test with active menu (returns filtered items)
  - Test time filtering (mock different times)
  - Test display order in response
  - Verify all existing filters still work
  - **Estimate:** 2 hours

- [ ] **Task 1.9:** Database Index Verification
  - Verify index on `menus(is_active)`
  - Verify composite indexes exist
  - Run EXPLAIN ANALYZE on new queries
  - **Estimate:** 30 minutes

**Deliverable:** Backend fully implements menu filtering

---

### Phase 2: Frontend Integration (Days 3-4)

**Priority: HIGH - User-facing changes**

#### Day 3 Morning
- [ ] **Task 2.1:** Create `useActiveMenu` hook
  - Implement hook file
  - Add API call to /api/kiosk/menu/active
  - Handle loading/error states
  - **Test:** Mock API responses
  - **Estimate:** 1 hour

- [ ] **Task 2.2:** Update Data Models
  - Update DTO interface
  - Update Domain model
  - Update ViewModel
  - **Test:** TypeScript compilation
  - **Estimate:** 30 minutes

- [ ] **Task 2.3:** Update Mappers
  - Add field mappings for display_order
  - Pass through start_at/end_at to domain
  - **Test:** Unit test mappers
  - **Estimate:** 30 minutes

#### Day 3 Afternoon
- [ ] **Task 2.4:** Implement Sorting
  - Add sorting logic to `useGetAvailableItems`
  - Sort by category_display_order first, then display_order
  - **Test:** Verify sort order with mock data
  - **Estimate:** 1 hour

- [ ] **Task 2.5:** Create NoMenuAvailable Component
  - Create component file
  - Add styling
  - Add logout handler
  - **Test:** Render test
  - **Estimate:** 1 hour

#### Day 4 Morning
- [ ] **Task 2.6:** Integrate Active Menu Check
  - Update main app component
  - Call useActiveMenu on mount
  - Show NoMenuAvailable if no menu
  - **Test:** E2E test with/without menu
  - **Estimate:** 1 hour

- [ ] **Task 2.7:** Optional: Display Menu Name
  - Show menu name in header
  - Add styling
  - **Estimate:** 30 minutes

#### Day 4 Afternoon
- [ ] **Task 2.8:** Frontend Testing
  - Test sorting visually
  - Test no menu error screen
  - Test SSE events still work
  - Test item updates
  - **Estimate:** 2 hours

**Deliverable:** Frontend fully integrated with menu system

---

### Phase 3: Testing & Edge Cases (Day 5)

**Priority: MEDIUM - Quality assurance**

- [ ] **Task 3.1:** Menu Switching Test
  - Deactivate menu → Verify error shown
  - Activate different menu → Verify items change
  - Test during active session
  - **Estimate:** 1 hour

- [ ] **Task 3.2:** Time-Based Filtering Test
  - Create items with start_at/end_at
  - Mock system time at different points
  - Verify items appear/disappear
  - **Estimate:** 1 hour

- [ ] **Task 3.3:** SSE Integration Test
  - Stock update for item in menu
  - Stock update for item NOT in menu
  - New item created in menu
  - Properties changed event
  - **Estimate:** 1.5 hours

- [ ] **Task 3.4:** Performance Testing
  - Load test with 100+ items
  - Measure query time
  - Check frontend render time
  - Verify no N+1 queries
  - **Estimate:** 1 hour

- [ ] **Task 3.5:** Error Handling Test
  - Network errors
  - Invalid token
  - Database errors
  - Menu deleted during session
  - **Estimate:** 1 hour

**Deliverable:** All edge cases tested and documented

---

### Phase 4: Documentation & Deployment (Day 6)

**Priority: LOW - Non-blocking**

- [ ] **Task 4.1:** Update API Documentation
  - Update Swagger descriptions
  - Add new endpoint docs
  - Update response examples
  - **Estimate:** 1 hour

- [ ] **Task 4.2:** Add Logging
  - Log active menu name on kiosk load
  - Log filter results (counts)
  - Log SSE events for debugging
  - **Estimate:** 1 hour

- [ ] **Task 4.3:** Create Migration Guide
  - Document changes for team
  - Create rollback plan
  - **Estimate:** 1 hour

- [ ] **Task 4.4:** Deploy to Staging
  - Deploy backend
  - Deploy frontend
  - Run smoke tests
  - **Estimate:** 2 hours

**Deliverable:** Production-ready deployment

---

### Total Effort Estimate

| Phase | Days | Hours |
|-------|------|-------|
| Phase 1: Backend Core | 2 | 12 |
| Phase 2: Frontend Integration | 2 | 10 |
| Phase 3: Testing & Edge Cases | 1 | 6 |
| Phase 4: Documentation & Deployment | 1 | 5 |
| **Total** | **6 days** | **33 hours** |

**Recommendation:** Plan for 7-8 days to account for unexpected issues

---

## 6. Database Query Changes

### 6.1 Current Query (No Menu Filtering)

```sql
-- Current: Returns ALL active items with stock
SELECT
    items_live.*,
    items_live_available.stock_quantity
FROM items_live
INNER JOIN items_live_available
    ON items_live.item_id = items_live_available.item_id
WHERE items_live.is_active = true
  AND items_live.is_archived = false
  AND items_live_available.stock_quantity > 0;
```

**Performance:**
- Scans: ~500 items (example)
- Query time: ~5ms

---

### 6.2 New Query (Menu-Filtered with Display Order)

```sql
-- New: Returns items in active menu with display order
SELECT
    items_live.*,
    items_live_available.stock_quantity,
    menu_items.display_order,
    menu_categories.display_order AS category_display_order,
    menu_items.start_at,
    menu_items.end_at
FROM items_live
INNER JOIN items_live_available
    ON items_live.item_id = items_live_available.item_id
INNER JOIN menu_items
    ON menu_items.item_id = items_live.item_id
INNER JOIN menu_categories
    ON menu_categories.food_category_name = items_live.food_category_name
    AND menu_categories.menu_id = menu_items.menu_id
WHERE menu_items.menu_id = (
    SELECT id FROM menus WHERE is_active = true LIMIT 1
)
  AND menu_categories.is_visible = true
  AND items_live.is_active = true
  AND items_live.is_archived = false
  AND items_live_available.stock_quantity > 0
  AND (menu_items.start_at IS NULL OR menu_items.start_at <= CURRENT_TIME)
  AND (menu_items.end_at IS NULL OR menu_items.end_at >= CURRENT_TIME)
ORDER BY menu_categories.display_order, menu_items.display_order;
```

**Changes:**
- ✅ Added menu_items join
- ✅ Added menu_categories join
- ✅ Added subquery for active menu
- ✅ Added time filtering
- ✅ Added ordering

**Expected Performance:**
- Scans: ~50-100 items in typical menu (80% reduction)
- Query time: ~8-10ms (with proper indexes)

---

### 6.3 Required Indexes

```sql
-- Verify these indexes exist (already created in menu migration)
CREATE INDEX IF NOT EXISTS ix_menus_is_active ON menus(is_active);
CREATE INDEX IF NOT EXISTS ix_menu_items_menu_id ON menu_items(menu_id);
CREATE INDEX IF NOT EXISTS ix_menu_items_item_id ON menu_items(item_id);
CREATE INDEX IF NOT EXISTS ix_menu_categories_menu_id ON menu_categories(menu_id);
CREATE INDEX IF NOT EXISTS ix_menu_categories_food_category_name
    ON menu_categories(food_category_name);

-- Composite indexes for optimal query performance
CREATE INDEX IF NOT EXISTS ix_menu_items_menu_order
    ON menu_items(menu_id, display_order);
CREATE INDEX IF NOT EXISTS ix_menu_categories_menu_order
    ON menu_categories(menu_id, display_order);
```

---

### 6.4 Query Execution Plan

```sql
-- Run this to analyze query performance
EXPLAIN ANALYZE
SELECT
    items_live.*,
    items_live_available.stock_quantity,
    menu_items.display_order,
    menu_categories.display_order AS category_display_order
FROM items_live
INNER JOIN items_live_available ON items_live.item_id = items_live_available.item_id
INNER JOIN menu_items ON menu_items.item_id = items_live.item_id
INNER JOIN menu_categories
    ON menu_categories.food_category_name = items_live.food_category_name
    AND menu_categories.menu_id = menu_items.menu_id
WHERE menu_items.menu_id = 1
  AND items_live.is_active = true
  AND items_live_available.stock_quantity > 0;
```

**Expected Plan:**
1. Index scan on `menus(is_active)` → single row
2. Index scan on `menu_items(menu_id)` → ~50 rows
3. Index lookup on `items_live(item_id)` → 50 lookups
4. Hash join with `items_live_available` → fast
5. Hash join with `menu_categories` → fast
6. Filter and sort → minimal cost

**Target:** < 15ms execution time

---

## 7. Edge Cases & Solutions

### 7.1 No Active Menu

**Scenario:** Admin deactivates all menus

**Backend Behavior:**
- `get_active_menu()` returns `None`
- `get_available_items_for_kiosk()` returns `[]`
- `get_all_food_categories()` returns `[]`
- `/api/kiosk/menu/active` returns `{has_active_menu: false}`

**Frontend Behavior:**
- `useActiveMenu()` sets `hasActiveMenu = false`
- App shows `<NoMenuAvailable />` screen
- User cannot proceed past login
- SSE connection still works (for future menu activation)

**Resolution:**
- Admin activates a menu
- Kiosk user clicks "Retry" or logs in again
- Items load normally

---

### 7.2 Item Removed from Menu

**Scenario:** Admin removes item from menu_items while kiosk session active

**Current State:**
- Item visible in kiosk
- User might have item in cart

**After Refetch:**
- Item not returned by `/api/kiosk/items/available`
- Frontend doesn't update existing state (only adds/updates)

**Solution Options:**

**Option A (Recommended):** Allow order completion
- Don't remove item from frontend state
- Item still orderable if in cart
- Only affects new sessions

**Option B:** Force refresh
- Add MENU_CHANGED SSE event
- Frontend refetches all items
- Removes items not in menu
- Risk: User loses cart

**Implementation (Option A):**
```typescript
// No special handling needed - natural behavior
```

**Implementation (Option B):**
```typescript
// Add MENU_CHANGED event handler
sseService.onEvent('MENU_CHANGED', () => {
  refetchItems()
  clearCart()
  showNotification('Menu has been updated')
})
```

---

### 7.3 Time Window Transition

**Scenario:** Item has start_at=06:00, end_at=11:00. Current time is 10:59.

**At 11:00:**
- Backend filters out item on next GET request
- Item still visible in frontend until refetch

**Solution 1: Client-Side Time Filtering**
```typescript
const isItemVisibleNow = (item: AvailableItemVM): boolean => {
  if (!item.startAt && !item.endAt) return true

  const now = new Date()
  const currentTime = `${now.getHours()}:${now.getMinutes()}:${now.getSeconds()}`

  if (item.startAt && currentTime < item.startAt) return false
  if (item.endAt && currentTime > item.endAt) return false

  return true
}

// Filter items before rendering
const visibleItems = items.filter(isItemVisibleNow)
```

**Solution 2: Periodic Refetch**
```typescript
// Refetch every 5 minutes to catch time changes
useEffect(() => {
  const interval = setInterval(() => {
    refetch()
  }, 5 * 60 * 1000) // 5 minutes

  return () => clearInterval(interval)
}, [refetch])
```

**Recommendation:** Use both for smooth UX

---

### 7.4 Menu Switch Mid-Session

**Scenario:** Admin deactivates Menu A, activates Menu B while kiosk active

**Current Behavior:**
- Kiosk still shows Menu A items
- No notification of change
- Next login gets Menu B

**Solution: Add MENU_CHANGED SSE Event**

**Backend:**
```python
# File: backend/app/models/SSEEventModels.py

class MenuChangedEvent(BaseModel):
    event_type: Literal["MENU_CHANGED"]
    new_menu_id: Optional[int]
    new_menu_name: Optional[str]
    timestamp: datetime

# Publish when menu activation changes
async def publish_menu_changed(menu: Optional[Menu]):
    event = MenuChangedEvent(
        event_type="MENU_CHANGED",
        new_menu_id=menu.id if menu else None,
        new_menu_name=menu.name if menu else None,
        timestamp=datetime.now()
    )
    await event_service._broadcast_to_all_kiosks(event)
```

**Frontend:**
```typescript
// In useGetAvailableItems hook
sseService.onEvent('MENU_CHANGED', async (data) => {
  console.log('Menu changed:', data)

  // Refetch items from new menu
  await refetch()

  // Show notification
  showNotification(`Menu updated: ${data.new_menu_name || 'No active menu'}`)

  // Optional: Clear cart
  if (confirm('Menu has changed. Clear cart?')) {
    clearCart()
  }
})
```

**Recommendation:** Implement in Phase 2 or 3

---

### 7.5 Item Added to Menu Mid-Session

**Scenario:** Admin adds new item to active menu

**Current Behavior:**
- ITEM_CREATED SSE event fires
- Frontend tries to add item
- Item might not be in menu

**New Behavior:**
- ITEM_CREATED SSE event fires
- Frontend checks if item in menu via GET /api/kiosk/items/{item_id}
- If in menu → Add to list
- If not in menu → Ignore

**Implementation:**
```typescript
// In handleItemUpdate (useGetAvailableItems)
case 'ITEM_CREATED':
  if (updateData.newItem) {
    // Check if item is in active menu
    try {
      const response = await fetch(`/api/kiosk/items/${updateData.itemId}`, {
        headers: { Authorization: `Bearer ${getAccessToken()}` }
      })

      if (response.ok) {
        const itemData = await response.json()
        const newItem = mapToViewModel(itemData)
        setItems(prev => [...prev, newItem])
      }
      // If 404, item not in menu - ignore
    } catch (err) {
      // Item not in menu, ignore
    }
  }
  break
```

---

### 7.6 Category Not in Menu but Item Is

**Scenario:** Data integrity issue - item references category not in menu_categories

**Prevention:** Foreign key constraints ensure this can't happen

**Constraint:**
```sql
-- Ensure menu_items.food_category_name exists in menu_categories
ALTER TABLE menu_items
ADD CONSTRAINT fk_menu_items_category_in_menu
FOREIGN KEY (menu_id, food_category_name)
REFERENCES menu_categories (menu_id, food_category_name);
```

**Backend Validation:**
```python
# When adding item to menu
if not category_exists_in_menu(menu_id, food_category_name):
    raise ValueError("Category must be added to menu first")
```

---

### 7.7 SSE Event for Item Not in Menu

**Scenario:** Stock update for item_id=999 arrives, but item not in current menu

**Current Behavior:**
- Frontend checks if item_id in items list
- Not found → Ignores or tries to fetch

**New Behavior (with menu filtering):**
- Frontend checks if item_id in items list
- Not found → Calls GET /api/kiosk/items/999
- Backend returns 404 (not in menu) → Frontend ignores
- Backend returns 200 (in menu) → Frontend adds item

**No changes needed** - current logic handles this gracefully

---

## 8. Testing Strategy

### 8.1 Backend Unit Tests

#### Test File: `tests/services/test_get_available_items_crud.py`

```python
def test_get_items_with_active_menu(db_session):
    """Test that only items in active menu are returned"""
    # Setup: Create menu, items, menu_items
    menu = create_test_menu(is_active=True)
    item1 = create_test_item()
    item2 = create_test_item()
    add_item_to_menu(menu, item1)
    # item2 NOT added to menu

    # Execute
    result = get_available_items_for_kiosk_db_crud.get_available_items_for_kiosk(db_session)

    # Assert
    assert len(result) == 1
    assert result[0][0].item_id == item1.item_id

def test_get_items_no_active_menu(db_session):
    """Test that empty list returned when no active menu"""
    # Setup: Deactivate all menus
    deactivate_all_menus(db_session)

    # Execute
    result = get_available_items_for_kiosk_db_crud.get_available_items_for_kiosk(db_session)

    # Assert
    assert result == []

def test_get_items_time_filtering(db_session, freezegun):
    """Test time-based filtering"""
    menu = create_test_menu(is_active=True)
    breakfast_item = create_test_item()
    add_item_to_menu(menu, breakfast_item, start_at="06:00", end_at="11:00")

    # Test at 10:00 - should appear
    freezegun.freeze("10:00:00")
    result = get_available_items_for_kiosk_db_crud.get_available_items_for_kiosk(db_session)
    assert len(result) == 1

    # Test at 12:00 - should NOT appear
    freezegun.freeze("12:00:00")
    result = get_available_items_for_kiosk_db_crud.get_available_items_for_kiosk(db_session)
    assert len(result) == 0

def test_display_order_returned(db_session):
    """Test that display orders are returned correctly"""
    menu = create_test_menu(is_active=True)
    category = create_test_category()
    add_category_to_menu(menu, category, display_order=5)

    item = create_test_item(category=category)
    add_item_to_menu(menu, item, display_order=3)

    result = get_available_items_for_kiosk_db_crud.get_available_items_for_kiosk(db_session)

    item_obj, display_order, category_display_order, _, _ = result[0]
    assert display_order == 3
    assert category_display_order == 5
```

---

### 8.2 Backend Integration Tests

#### Test File: `tests/api/test_kiosk_items_endpoint.py`

```python
def test_get_available_items_with_menu(client, auth_headers):
    """Test GET /api/kiosk/items/available with active menu"""
    # Setup
    setup_active_menu_with_items()

    # Execute
    response = client.get("/api/kiosk/items/available", headers=auth_headers)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert "display_order" in data[0]
    assert "category_display_order" in data[0]

def test_get_available_items_no_menu(client, auth_headers):
    """Test GET /api/kiosk/items/available with no active menu"""
    # Setup
    deactivate_all_menus()

    # Execute
    response = client.get("/api/kiosk/items/available", headers=auth_headers)

    # Assert
    assert response.status_code == 200
    assert response.json() == []

def test_get_active_menu_info(client, auth_headers):
    """Test GET /api/kiosk/menu/active"""
    # Setup
    menu = create_active_menu(name="Breakfast Menu")

    # Execute
    response = client.get("/api/kiosk/menu/active", headers=auth_headers)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["has_active_menu"] is True
    assert data["menu"]["name"] == "Breakfast Menu"
```

---

### 8.3 Frontend Unit Tests

#### Test File: `tests/hooks/useActiveMenu.test.ts`

```typescript
describe('useActiveMenu', () => {
  it('should return active menu when available', async () => {
    // Mock API
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        has_active_menu: true,
        menu: { id: 1, name: 'Test Menu', description: null }
      })
    })

    const { result, waitForNextUpdate } = renderHook(() => useActiveMenu())

    expect(result.current.loading).toBe(true)

    await waitForNextUpdate()

    expect(result.current.hasActiveMenu).toBe(true)
    expect(result.current.menuInfo?.name).toBe('Test Menu')
    expect(result.current.loading).toBe(false)
  })

  it('should handle no active menu', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        has_active_menu: false,
        menu: null
      })
    })

    const { result, waitForNextUpdate } = renderHook(() => useActiveMenu())

    await waitForNextUpdate()

    expect(result.current.hasActiveMenu).toBe(false)
    expect(result.current.menuInfo).toBe(null)
  })
})
```

---

### 8.4 Frontend Integration Tests

#### Test File: `tests/integration/menu-flow.test.tsx`

```typescript
describe('Menu Integration Flow', () => {
  it('should show error when no active menu', async () => {
    mockAPI.getActiveMenu.mockResolvedValue({ has_active_menu: false, menu: null })

    render(<KioskApp />)

    await waitFor(() => {
      expect(screen.getByText(/no active menu/i)).toBeInTheDocument()
    })
  })

  it('should load items when menu is active', async () => {
    mockAPI.getActiveMenu.mockResolvedValue({
      has_active_menu: true,
      menu: { id: 1, name: 'Test Menu' }
    })
    mockAPI.getAvailableItems.mockResolvedValue([
      { item_id: 1, name_ru: 'Coffee', display_order: 1, category_display_order: 1 }
    ])

    render(<KioskApp />)

    await waitFor(() => {
      expect(screen.getByText('Coffee')).toBeInTheDocument()
    })
  })

  it('should sort items by display order', async () => {
    mockAPI.getAvailableItems.mockResolvedValue([
      { item_id: 2, name_ru: 'Tea', display_order: 2, category_display_order: 1 },
      { item_id: 1, name_ru: 'Coffee', display_order: 1, category_display_order: 1 }
    ])

    render(<KioskApp />)

    await waitFor(() => {
      const items = screen.getAllByTestId('menu-item')
      expect(items[0]).toHaveTextContent('Coffee')
      expect(items[1]).toHaveTextContent('Tea')
    })
  })
})
```

---

### 8.5 E2E Tests

#### Test File: `e2e/menu-kiosk.spec.ts`

```typescript
test('Full menu flow - login to order', async ({ page }) => {
  // Login
  await page.goto('/login')
  await page.fill('[name="username"]', 'kiosk1')
  await page.fill('[name="password"]', 'password')
  await page.click('button[type="submit"]')

  // Should see menu items
  await expect(page.locator('[data-testid="menu-item"]')).toHaveCount.greaterThan(0)

  // Items should be sorted by display order
  const firstItem = page.locator('[data-testid="menu-item"]').first()
  await expect(firstItem).toBeVisible()

  // Add item to cart
  await firstItem.click()
  await page.click('[data-testid="add-to-cart"]')

  // Verify cart
  await expect(page.locator('[data-testid="cart-count"]')).toHaveText('1')
})

test('No menu error handling', async ({ page }) => {
  // Deactivate menu via API
  await apiHelper.deactivateAllMenus()

  // Login
  await page.goto('/login')
  await loginAsKiosk(page)

  // Should see error
  await expect(page.locator('text=No Menu Available')).toBeVisible()
  await expect(page.locator('[data-testid="menu-item"]')).toHaveCount(0)
})
```

---

### 8.6 Performance Tests

```typescript
describe('Performance Tests', () => {
  it('should load 100 items in under 2 seconds', async () => {
    const items = generateMockItems(100)
    mockAPI.getAvailableItems.mockResolvedValue(items)

    const start = performance.now()
    render(<KioskApp />)

    await waitFor(() => {
      expect(screen.getAllByTestId('menu-item')).toHaveLength(100)
    })

    const duration = performance.now() - start
    expect(duration).toBeLessThan(2000)
  })

  it('should sort 100 items efficiently', () => {
    const items = generateRandomOrderItems(100)

    const start = performance.now()
    const sorted = sortItemsByDisplayOrder(items)
    const duration = performance.now() - start

    expect(duration).toBeLessThan(10) // < 10ms for sorting
    expect(sorted[0].displayOrder).toBeLessThanOrEqual(sorted[1].displayOrder)
  })
})
```

---

## 9. Performance Considerations

### 9.1 Database Query Performance

**Current Query (No Menu):**
- Table scans: 1 (items_live)
- Rows scanned: ~500
- Time: ~5ms

**New Query (Menu-Filtered):**
- Table scans: 4 (items_live, menu_items, menu_categories, menus)
- Rows scanned: ~100 (after menu filtering)
- Joins: 3
- Expected time: ~8-12ms (with indexes)

**Optimization:**
- ✅ Indexes on all join columns
- ✅ Composite indexes for ORDER BY
- ✅ Subquery for active menu is indexed
- ✅ LIMIT 1 on active menu subquery

**Monitoring:**
```python
import time

def get_available_items_for_kiosk(self, db: Session):
    start = time.time()
    result = # ... query ...
    duration = time.time() - start

    logger.info(f"Query time: {duration*1000:.2f}ms, items returned: {len(result)}")

    if duration > 0.02:  # > 20ms
        logger.warning(f"Slow query detected: {duration*1000:.2f}ms")

    return result
```

---

### 9.2 Frontend Performance

**Sorting Performance:**
```typescript
// 100 items, 2 levels of sorting
// Expected: < 1ms

const sortedItems = useMemo(() => {
  const start = performance.now()

  const sorted = [...items].sort((a, b) => {
    if (a.categoryDisplayOrder !== b.categoryDisplayOrder) {
      return a.categoryDisplayOrder - b.categoryDisplayOrder
    }
    return a.displayOrder - b.displayOrder
  })

  const duration = performance.now() - start
  if (duration > 5) {
    console.warn(`Slow sorting: ${duration}ms for ${items.length} items`)
  }

  return sorted
}, [items])
```

**Render Performance:**
- Use `React.memo` for item components
- Virtualize list if > 50 items (optional)
- Lazy load images

```typescript
const MemoizedMenuItem = React.memo(MenuItem, (prev, next) => {
  return prev.itemId === next.itemId &&
         prev.stockQuantity === next.stockQuantity &&
         prev.priceGross === next.priceGross
})
```

---

### 9.3 SSE Performance

**No changes to SSE:**
- Still broadcasts to all kiosks
- Client-side filtering negligible (< 1ms)
- Trade-off: Higher bandwidth vs. server complexity

**Bandwidth Impact:**
```
Current: 1 SSE event → N kiosks (all receive)
New:     1 SSE event → N kiosks (all receive, frontend filters)

Alternative (not recommended):
         1 SSE event → N kiosks (server filters per kiosk menu)
         Requires tracking kiosk→menu mapping
         Adds server complexity
```

**Recommendation:** Keep global broadcast (simpler, scales well)

---

### 9.4 Caching Strategy

**Backend Caching (Optional):**
```python
from functools import lru_cache
from datetime import datetime, timedelta

# Cache active menu for 1 minute
@lru_cache(maxsize=1)
def get_cached_active_menu(timestamp_minute: str):
    return db.query(Menu).filter(Menu.is_active == True).first()

def get_available_items_for_kiosk(self, db: Session):
    # Round to minute for cache key
    cache_key = datetime.now().strftime("%Y-%m-%d %H:%M")
    active_menu = get_cached_active_menu(cache_key)
    # ... rest of query
```

**Frontend Caching:**
- Already implemented (localStorage with 4-hour TTL)
- No changes needed

---

## 10. Summary

### What We Already Have ✅

1. Menu tables with proper schema
2. Menu activation/deactivation logic
3. Display order columns
4. Time filtering columns (start_at/end_at)
5. SSE infrastructure (7 event types)
6. Frontend state management
7. Database indexes

### What We Need to Add 🔴

#### Backend (5 Changes)
1. Modify `GetAvailableItemsForKioskDBCRUD` - Add menu filtering
2. Update `KioskAvailableItemsResponseModel` - Add 4 fields
3. Modify `KioskCategoriesDBCRUD` - Add menu filtering
4. Create `KioskActiveMenuEndpoint` - New endpoint
5. Update existing `KioskItemDetailDBCRUD.get_item_by_id()` - Add menu filtering to existing method
6. Update logic layers to handle tuples

#### Frontend (5 Changes)
1. Create `useActiveMenu` hook - Check for active menu
2. Update data models (DTO/Domain/VM) - Add display_order fields
3. Update mappers - Pass through new fields
4. Implement sorting - Sort by display_order
5. Create `NoMenuAvailable` component - Error screen

### Effort Estimate

- **Backend:** 12 hours (2 days)
- **Frontend:** 10 hours (1.5 days)
- **Testing:** 6 hours (1 day)
- **Documentation:** 5 hours (0.5 days)
- **Total:** 33 hours (5 days)

**Recommended Timeline:** 6-7 days with buffer

---

## 11. Next Steps

1. **Review this document** with the development team
2. **Create tickets** for each task in the implementation plan
3. **Set up test environment** with sample menu data
4. **Start Phase 1** (Backend core) - highest priority
5. **Daily standups** to track progress
6. **Code reviews** for each phase before merging
7. **Staging deployment** after Phase 2 complete
8. **Production deployment** after all testing passes

---

## 12. Questions & Decisions

### Decisions Made

1. ✅ **SSE Events:** Keep unchanged, client-side filtering
2. ✅ **Time Filtering:** Both server-side (on fetch) and client-side (between fetches)
3. ✅ **No Menu Fallback:** Show error, don't allow past login
4. ✅ **Display Order:** Sort client-side after fetching
5. ✅ **Menu Switch:** Add optional MENU_CHANGED event (Phase 3)

### Open Questions

1. **Menu Switch Behavior:** Should kiosk auto-refresh or require re-login?
   - **Recommendation:** Auto-refresh with notification (Phase 3)

2. **Item Removal from Menu:** Allow completing orders or force refresh?
   - **Recommendation:** Allow completion (Option A)

3. **Empty Categories:** Show or hide in menu?
   - **Recommendation:** Hide (better UX)

4. **Performance Target:** What's acceptable query time?
   - **Recommendation:** < 15ms for items query

---

## Document Metadata

- **Version:** 1.0
- **Created:** 2025-10-22
- **Author:** Development Team + AI Assistant
- **Status:** Ready for Review
- **Next Review:** After Phase 1 completion

---

## Appendix: File Reference

### Backend Files to Modify

| Priority | File | Change |
|----------|------|--------|
| CRITICAL | `services/GetAvailableItemsForKioskDBCRUD.py` | Add menu filtering query |
| CRITICAL | `models/KioskAvailableItemsResponseModel.py` | Add 4 new fields |
| CRITICAL | `logic/GetAvailableItemsForKioskLogic.py` | Handle tuple unpacking |
| HIGH | `services/KioskCategoriesDBCRUD.py` | Add menu filtering |
| HIGH | `models/KioskCategoriesPydanticModel.py` | Add display_order field |
| HIGH | `logic/KioskCategoriesLogic.py` | Handle tuple unpacking |
| HIGH | `api/KioskActiveMenuEndpoint.py` | Create new endpoint (NEW FILE) |
| MEDIUM | `services/KioskItemDetailDBCRUD.py` | ✅ Update existing get_item_by_id() with menu filtering |
| MEDIUM | `logic/KioskItemDetailLogic.py` | ✅ Update to handle tuple response |

### Frontend Files to Modify

| Priority | File | Change |
|----------|------|--------|
| HIGH | `hooks/useActiveMenu.ts` | Create new hook |
| HIGH | `models/dto/getAvailableItems.dto.ts` | Add fields |
| HIGH | `models/domain/availableItem.ts` | Add fields |
| HIGH | `models/view/availableItem.vm.ts` | Add fields |
| HIGH | `services/mappers/getAvailableItems.mappers.ts` | Update mappings |
| HIGH | `hooks/useGetAvailableItems.ts` | Add sorting |
| HIGH | `components/NoMenuAvailable.tsx` | Create component |
| HIGH | `App.tsx` | Integrate menu check |

---

**End of Document**
