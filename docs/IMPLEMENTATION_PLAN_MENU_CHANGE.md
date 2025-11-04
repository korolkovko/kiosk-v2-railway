# Menu Change via SSE - Implementation Plan

## Overview

Implement automatic menu switching via SSE events, allowing backend to activate new menus (e.g., Breakfast → Lunch) with kiosks automatically downloading new media and updating UI in real-time.

**Key Requirements:**
- ✅ Works silently during service mode (no UI changes, background download)
- ✅ Shows loading UI during normal operation
- ✅ Incremental media download (only new items/categories)
- ✅ Keep all media (Option 1 - no cleanup)
- ✅ Handles edge cases (active orders, transitions)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    BACKEND (Python)                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Admin Panel:                                                │
│  POST /api/v1/admin/menu/activate                            │
│    ↓                                                          │
│  MenuActivationLogic:                                        │
│    1. Set menu.is_active = True                              │
│    2. Get menu items/categories                              │
│    3. Create MenuActivatedEvent                              │
│    4. Publish to "kiosk_broadcast" channel                   │
│                                                               │
│  SSE Event:                                                  │
│  {                                                            │
│    event_type: "MENU_ACTIVATED",                             │
│    menu_id: 5,                                               │
│    menu_name: "Lunch Menu",                                  │
│    active_from: "11:00:00",                                  │
│    active_to: "15:00:00",                                    │
│    requires_full_refresh: true,                              │
│    timestamp: "2025-10-26T11:00:00.000Z"                     │
│  }                                                            │
│                                                               │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ SSE Stream
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (React)                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  useSSEMenuUpdates Hook:                                     │
│    1. Receive MENU_ACTIVATED event                           │
│    2. Check if service mode active                           │
│                                                               │
│  If Service Mode Active:                                     │
│    → Silent background refresh                               │
│    → No UI changes                                           │
│    → Download new media                                      │
│    → Update ItemsContext                                     │
│                                                               │
│  If Normal Operation:                                        │
│    → Show loading overlay: "Updating menu..."                │
│    → Fetch new menu data                                     │
│    → Compare with current items/categories                   │
│    → Download only NEW media (incremental)                   │
│    → Update ItemsContext                                     │
│    → Fade in new menu                                        │
│                                                               │
│  If During Active Order:                                     │
│    → Queue the menu change                                   │
│    → Let user complete order                                 │
│    → Apply menu change after order completion                │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Backend Implementation

### Step 1: Add SSE Event Model

**File:** `backend/app/models/SSEEventModels.py`

**Add new event class:**

```python
class MenuActivatedEvent(BaseModel):
    """Event when a new menu becomes active"""
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})

    event_type: Literal["MENU_ACTIVATED"] = "MENU_ACTIVATED"
    menu_id: int
    menu_name: str
    active_from: str  # HH:MM:SS format
    active_to: str    # HH:MM:SS format
    requires_full_refresh: bool  # True = new items/categories, False = just item updates
    timestamp: datetime = Field(default_factory=datetime.utcnow)
```

**Update SSEEvent Union:**

```python
# At the end of SSEEventModels.py
SSEEvent = Union[
    ItemStatusChangedEvent,
    ItemPromotionChangedEvent,
    ItemStockChangedEvent,
    ItemCreatedEvent,
    ItemPropertiesChangedEvent,
    OrderStatusChangedEvent,
    OrderEventTriggeredEvent,
    KioskServiceModeChangedEvent,
    MenuActivatedEvent  # ← Add this
]
```

---

### Step 2: Create Menu Event Service

**File:** `backend/app/services/MenuEventService.py` (NEW)

```python
# MenuEventService.py
# Service for broadcasting menu-related SSE events

from ..models.SSEEventModels import MenuActivatedEvent, SSEEvent
from ..websockets.event_bus import bus
from typing import Optional

class MenuEventService:
    """Service for menu-related SSE events"""

    KIOSK_BROADCAST_CHANNEL = "kiosk_broadcast"

    async def broadcast_menu_activated(
        self,
        menu_id: int,
        menu_name: str,
        active_from: str,
        active_to: str,
        requires_full_refresh: bool = True
    ) -> None:
        """
        Broadcast menu activation event to all connected kiosks

        Args:
            menu_id: ID of the activated menu
            menu_name: Display name of the menu
            active_from: Start time (HH:MM:SS)
            active_to: End time (HH:MM:SS)
            requires_full_refresh: True if kiosks should download new media
        """
        try:
            event = MenuActivatedEvent(
                menu_id=menu_id,
                menu_name=menu_name,
                active_from=active_from,
                active_to=active_to,
                requires_full_refresh=requires_full_refresh
            )

            # Use mode='json' to apply json_encoders (datetime → ISO string)
            event_dict = event.model_dump(mode='json')

            print(f"📋 PUBLISHING MENU ACTIVATED EVENT: menu_id={menu_id}, name={menu_name}")
            print(f"🔍 EVENT BUS SUBSCRIBERS: {len(bus._subs.get(self.KIOSK_BROADCAST_CHANNEL, set()))} active subscribers")

            await bus.publish(self.KIOSK_BROADCAST_CHANNEL, event_dict)

            print(f"✅ MENU EVENT PUBLISHED to {len(bus._subs.get(self.KIOSK_BROADCAST_CHANNEL, set()))} subscribers")

        except Exception as e:
            print(f"❌ Failed to broadcast menu activated event: {str(e)}")
            # Don't raise - menu activation should succeed even if SSE fails

# Global service instance
menu_event_service = MenuEventService()
```

---

### Step 3: Add Menu Activation Logic

**File:** `backend/app/logic/MenuLogic.py` or existing menu management file

**Add to menu activation function:**

```python
from ..services.MenuEventService import menu_event_service

async def activate_menu(db: Session, menu_id: int, current_user: User):
    """
    Activate a menu and broadcast SSE event to all kiosks
    """
    try:
        # 1. Get menu from database
        menu = db.query(Menu).filter(Menu.id == menu_id).first()
        if not menu:
            raise HTTPException(status_code=404, detail="Menu not found")

        # 2. Deactivate all other menus
        db.query(Menu).update({Menu.is_active: False})

        # 3. Activate this menu
        menu.is_active = True
        db.commit()

        # 4. Broadcast SSE event to all kiosks
        await menu_event_service.broadcast_menu_activated(
            menu_id=menu.id,
            menu_name=menu.name,
            active_from=str(menu.active_from),
            active_to=str(menu.active_to),
            requires_full_refresh=True  # Always true for now
        )

        print(f"✅ Menu '{menu.name}' activated and broadcasted to kiosks")

        return menu

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to activate menu: {str(e)}")
```

---

## Phase 2: Frontend Implementation

### Step 1: Update SSE Types

**File:** `frontend/apps/kiosk/src/SSESubscription/sseService.ts`

**Add to event type union:**

```typescript
export type KioskSSEEvent =
  | {
      event_type: 'ITEM_STATUS_CHANGED'
      item_id: number
      is_active: boolean
      timestamp: string
    }
  // ... other event types ...
  | {
      event_type: 'KIOSK_SERVICE_MODE_CHANGED'
      kiosk_username: string
      is_service_mode: boolean
      service_picture_name: string | null
      timestamp: string
    }
  | {
      event_type: 'MENU_ACTIVATED'  // ← Add this
      menu_id: number
      menu_name: string
      active_from: string
      active_to: string
      requires_full_refresh: boolean
      timestamp: string
    }
```

---

### Step 2: Create Menu Updates Hook

**File:** `frontend/apps/kiosk/src/SSESubscription/useSSEMenuUpdates.ts` (NEW)

```typescript
// useSSEMenuUpdates.ts
// React hook for managing SSE-based menu change events

import { useEffect, useCallback } from 'react'
import { sseService, type KioskSSEEvent } from './sseService'

export interface MenuUpdateData {
  menuId: number
  menuName: string
  activeFrom: string
  activeTo: string
  requiresFullRefresh: boolean
  timestamp: string
}

export interface UseSSEMenuUpdatesProps {
  onMenuActivated: (data: MenuUpdateData) => Promise<void>
}

export function useSSEMenuUpdates({
  onMenuActivated
}: UseSSEMenuUpdatesProps) {

  const handleSSEEvent = useCallback(async (event: KioskSSEEvent) => {
    if (event.event_type !== 'MENU_ACTIVATED') return

    console.log('📋 MENU_ACTIVATED SSE event received:', event)

    await onMenuActivated({
      menuId: event.menu_id,
      menuName: event.menu_name,
      activeFrom: event.active_from,
      activeTo: event.active_to,
      requiresFullRefresh: event.requires_full_refresh,
      timestamp: event.timestamp
    })
  }, [onMenuActivated])

  useEffect(() => {
    // Ensure SSE connection is established
    if (!sseService.isConnected()) {
      sseService.connect()
    }

    // Set up event handler
    sseService.onEvent('MENU_ACTIVATED', handleSSEEvent)

    // Cleanup on unmount
    return () => {
      // Note: We don't disconnect the SSE service here since it's shared
    }
  }, [handleSSEEvent])

  return {
    isConnected: sseService.isConnected(),
    disconnect: () => sseService.disconnect(),
    reconnect: () => sseService.connect()
  }
}
```

---

### Step 3: Create Menu Refresh Logic

**File:** `frontend/apps/kiosk/src/services/menuRefresh.service.ts` (NEW)

```typescript
// menuRefresh.service.ts
// Service for handling menu changes and media updates

import { mediaCacheService } from './mediaCache.service'
import { getAllMenuItemsForPreload } from '../api/getAllMenuItemsForPreload.api'

export interface MenuRefreshOptions {
  onProgress?: (message: string) => void
}

export class MenuRefreshService {

  /**
   * Identify new items that need media download
   */
  private identifyNewItems(
    currentItemIds: number[],
    newItemIds: number[]
  ): number[] {
    return newItemIds.filter(id => !currentItemIds.includes(id))
  }

  /**
   * Identify new categories that need media download
   */
  private identifyNewCategories(
    currentCategories: string[],
    newCategories: string[]
  ): string[] {
    return newCategories.filter(cat => !currentCategories.includes(cat))
  }

  /**
   * Perform full menu refresh with incremental media download
   * Only downloads media for NEW items/categories (not re-downloading existing)
   */
  async performFullRefresh(
    currentItemIds: number[],
    currentCategories: string[],
    options: MenuRefreshOptions = {}
  ): Promise<{itemIds: number[], categories: string[]}> {

    try {
      options.onProgress?.('Fetching new menu data...')

      // 1. Fetch new menu data from backend
      console.log('📡 Fetching new menu data...')
      const menuData = await getAllMenuItemsForPreload()

      // 2. Identify what's new
      const newItemIds = this.identifyNewItems(currentItemIds, menuData.item_ids)
      const newCategories = this.identifyNewCategories(
        currentCategories,
        ['NEW', ...menuData.category_names]  // Include synthetic NEW category
      )

      console.log(`📊 Menu comparison:`)
      console.log(`  - Current items: ${currentItemIds.length}`)
      console.log(`  - New menu items: ${menuData.item_ids.length}`)
      console.log(`  - Items to download: ${newItemIds.length}`)
      console.log(`  - Current categories: ${currentCategories.length}`)
      console.log(`  - New menu categories: ${menuData.category_names.length}`)
      console.log(`  - Categories to download: ${newCategories.length}`)

      // 3. Download only NEW media (incremental)
      if (newItemIds.length > 0 || newCategories.length > 0) {
        options.onProgress?.(`Downloading ${newItemIds.length} new items and ${newCategories.length} new categories...`)

        console.log('📥 Downloading NEW media only (incremental)...')

        await mediaCacheService.downloadAllMedia(
          newCategories,
          newItemIds,
          (progress) => {
            options.onProgress?.(
              `Downloading: ${progress.current}/${progress.total} - ${progress.currentItem}`
            )
          }
        )

        console.log('✅ New media downloaded successfully')
      } else {
        console.log('ℹ️ No new media to download, menu items unchanged')
      }

      return {
        itemIds: menuData.item_ids,
        categories: ['NEW', ...menuData.category_names]
      }

    } catch (error) {
      console.error('❌ Menu refresh failed:', error)
      throw error
    }
  }
}

// Global service instance
export const menuRefreshService = new MenuRefreshService()
```

---

### Step 4: Integrate in App Component

**File:** `frontend/apps/kiosk/src/App.tsx` (or create dedicated `MenuRefreshHandler` component)

```typescript
import { useState, useCallback } from 'react'
import { useSSEMenuUpdates, type MenuUpdateData } from './SSESubscription/useSSEMenuUpdates'
import { menuRefreshService } from './services/menuRefresh.service'
import { useItems } from './contexts/ItemsContext'
import { useServiceModeStore } from './stores/ServiceModeStore'

// Add state for menu refresh UI
const [isRefreshingMenu, setIsRefreshingMenu] = useState(false)
const [menuRefreshProgress, setMenuRefreshProgress] = useState<string | null>(null)

// Get current data
const { items, refetch: refetchItems } = useItems()
const { isActive: isServiceModeActive } = useServiceModeStore()

/**
 * Handle menu activation event from SSE
 */
const handleMenuActivated = useCallback(async (data: MenuUpdateData) => {
  console.log('📋 Menu activated:', data.menuName)

  if (!data.requiresFullRefresh) {
    // Simple case: just refetch items (no new media needed)
    console.log('ℹ️ Menu update without new media, just refetching...')
    await refetchItems()
    return
  }

  // Check if service mode is active
  if (isServiceModeActive) {
    // During service mode: download silently, no UI changes
    console.log('🛠️ Service mode active, refreshing menu silently in background...')
    await performSilentMenuRefresh(data)
  } else {
    // Normal operation: show loading UI
    console.log('🔄 Normal operation, showing loading UI for menu refresh...')
    await performVisibleMenuRefresh(data)
  }
}, [items, isServiceModeActive, refetchItems])

/**
 * Perform menu refresh with visible loading UI
 */
const performVisibleMenuRefresh = async (data: MenuUpdateData) => {
  setIsRefreshingMenu(true)
  setMenuRefreshProgress('Preparing to update menu...')

  try {
    // Get current item IDs and categories
    const currentItemIds = items.map(item => item.itemId)
    const currentCategories = [...new Set(items.map(item => item.foodCategory))]

    // Perform refresh with progress updates
    await menuRefreshService.performFullRefresh(
      currentItemIds,
      currentCategories,
      {
        onProgress: (message) => setMenuRefreshProgress(message)
      }
    )

    // Refetch items to update UI
    setMenuRefreshProgress('Updating display...')
    await refetchItems()

    // Show success message briefly
    setMenuRefreshProgress(`Menu updated to: ${data.menuName}`)
    setTimeout(() => {
      setIsRefreshingMenu(false)
      setMenuRefreshProgress(null)
    }, 2000)

    console.log(`✅ Menu refresh complete: ${data.menuName}`)

  } catch (error) {
    console.error('❌ Menu refresh failed:', error)
    setMenuRefreshProgress('Error updating menu. Please refresh manually.')
    setTimeout(() => {
      setIsRefreshingMenu(false)
      setMenuRefreshProgress(null)
    }, 5000)
  }
}

/**
 * Perform menu refresh silently during service mode
 */
const performSilentMenuRefresh = async (data: MenuUpdateData) => {
  try {
    const currentItemIds = items.map(item => item.itemId)
    const currentCategories = [...new Set(items.map(item => item.foodCategory))]

    // Download in background without UI updates
    await menuRefreshService.performFullRefresh(
      currentItemIds,
      currentCategories
    )

    // Update context silently
    await refetchItems()

    console.log(`✅ Silent menu refresh complete during service mode: ${data.menuName}`)

  } catch (error) {
    console.error('❌ Silent menu refresh failed:', error)
    // Don't show error UI during service mode
  }
}

// Hook up SSE listener
useSSEMenuUpdates({
  onMenuActivated: handleMenuActivated
})

// Add loading overlay to JSX (only shown during normal operation)
{isRefreshingMenu && (
  <div className="fixed inset-0 bg-black bg-opacity-75 z-50 flex items-center justify-center">
    <div className="bg-white rounded-lg p-8 max-w-md">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
      <p className="text-center text-gray-700 font-medium">
        {menuRefreshProgress || 'Updating menu...'}
      </p>
    </div>
  </div>
)}
```

---

## Phase 3: Edge Cases & Enhancements

### Edge Case 1: Menu Change During Active Order

```typescript
// In order processing logic
const { isPendingMenuChange, applyPendingMenuChange } = useMenuChangeQueue()

// When order completes
const handleOrderComplete = async () => {
  // Order is finished, safe to apply menu change
  if (isPendingMenuChange) {
    await applyPendingMenuChange()
  }
}

// In menu change handler
const handleMenuActivated = async (data: MenuUpdateData) => {
  const { hasActiveOrder } = useOrderStore.getState()

  if (hasActiveOrder) {
    // Queue the change, don't apply immediately
    console.log('📦 Order in progress, queuing menu change...')
    queueMenuChange(data)
    // Show notification: "Menu will update after order completes"
    return
  }

  // Normal handling
  await performMenuRefresh(data)
}
```

---

### Edge Case 2: Service Mode Ends After Menu Change

```typescript
// In ServiceModeEventBridge or service mode deactivation handler
const handleServiceModeDeactivated = async () => {
  // Check if menu was changed during service mode
  const menuChangedDuringServiceMode = getMenuChangeFlag()

  if (menuChangedDuringServiceMode) {
    // Show brief notification
    showNotification(`Menu updated to: ${getLatestMenuName()}`, 3000)
    clearMenuChangeFlag()
  }
}
```

---

### Enhancement 1: Preload Next Menu (Future)

```python
# Backend: Send preload event 5 minutes before activation
class MenuPreloadEvent(BaseModel):
    event_type: Literal["MENU_PRELOAD"] = "MENU_PRELOAD"
    menu_id: int
    menu_name: str
    activates_at: str  # ISO timestamp

# Schedule preload 5 minutes early
schedule_event(
    time=menu.active_from - timedelta(minutes=5),
    event=MenuPreloadEvent(...)
)
```

```typescript
// Frontend: Download in background before activation
const handleMenuPreload = async (data: MenuPreloadData) => {
  console.log(`⏰ Preloading menu "${data.menuName}" (activates at ${data.activatesAt})`)

  // Download media in background
  await menuRefreshService.performFullRefresh(
    currentItemIds,
    currentCategories,
    { silent: true }
  )

  console.log('✅ Menu preloaded, ready for instant activation')
}
```

---

### Enhancement 2: Differential Updates (Future)

```python
# Backend: Include specific item changes
class MenuActivatedEvent(BaseModel):
    # ... existing fields ...
    added_item_ids: list[int] | None = None
    removed_item_ids: list[int] | None = None
    updated_item_ids: list[int] | None = None
```

```typescript
// Frontend: Process only changed items
if (event.added_item_ids) {
  await downloadItemsMedia(event.added_item_ids)
}
if (event.removed_item_ids) {
  // Optionally remove from cache (but we decided to keep all - Option 1)
}
```

---

## Testing Plan

### Test Scenario 1: Normal Operation Menu Change
```
1. Kiosk on main screen showing Breakfast menu
2. Backend activates Lunch menu at 11:00 AM
3. Expected:
   - Loading overlay appears: "Updating menu..."
   - New items download (progress shown)
   - UI updates to show Lunch items
   - Loading overlay disappears
```

### Test Scenario 2: Service Mode Menu Change
```
1. Kiosk in service mode (showing maintenance picture)
2. Backend activates Lunch menu
3. Expected:
   - No UI changes (still showing maintenance)
   - Console logs show silent download
   - When service mode ends: Lunch menu displayed
   - Optional: Brief notification "Menu updated to: Lunch Menu"
```

### Test Scenario 3: Menu Change During Order
```
1. User is building order (items in cart)
2. Backend activates new menu
3. Expected:
   - Menu change queued (not applied immediately)
   - User can complete order with current menu items
   - After order completes: menu updates
   - Notification: "Menu has been updated"
```

### Test Scenario 4: Multiple Rapid Menu Changes
```
1. Backend activates Menu A
2. Before download completes, activates Menu B
3. Expected:
   - Cancel Menu A download
   - Start Menu B download
   - Only Menu B applied
```

### Test Scenario 5: Network Failure During Download
```
1. Menu change starts
2. Network drops during media download
3. Expected:
   - Show error message
   - Keep current menu active
   - User can retry or continue with old menu
```

---

## Rollout Strategy

### Phase 1: MVP (Week 1)
- ✅ Backend: Add MENU_ACTIVATED event
- ✅ Frontend: Add useSSEMenuUpdates hook
- ✅ Frontend: Basic menu refresh (visible loading)
- ✅ Test with 1-2 kiosks

### Phase 2: Silent Mode (Week 2)
- ✅ Add silent refresh during service mode
- ✅ Add menu change queueing during orders
- ✅ Test edge cases

### Phase 3: Polish (Week 3)
- ✅ Add progress indicators
- ✅ Add notifications
- ✅ Add error handling
- ✅ Full testing with all kiosks

### Phase 4: Future Enhancements
- ⏳ Preload next menu (5 min early)
- ⏳ Differential updates
- ⏳ Analytics (track menu changes)

---

## Monitoring & Metrics

### Backend Metrics
```python
# Track menu activations
menu_activation_count = 0
menu_activation_errors = 0
kiosks_notified_per_activation = []

# Log for monitoring
print(f"📊 Menu Activation Metrics:")
print(f"  - Total activations: {menu_activation_count}")
print(f"  - Errors: {menu_activation_errors}")
print(f"  - Avg kiosks notified: {sum(kiosks_notified_per_activation)/len(...)}")
```

### Frontend Metrics
```typescript
// Track menu changes
const menuChangeMetrics = {
  totalChanges: 0,
  successfulChanges: 0,
  failedChanges: 0,
  averageDownloadTime: 0,
  silentChanges: 0,  // During service mode
  queuedChanges: 0   // During orders
}
```

---

## Documentation

### For Admins
```
# How to Activate a New Menu

1. Go to Admin Panel → Menu Management
2. Select the menu to activate (e.g., "Lunch Menu")
3. Click "Activate Menu"
4. All connected kiosks will automatically:
   - Download new item media (if needed)
   - Update their display
   - Show the new menu to customers

# During Service Mode
- Kiosks in service mode will update silently
- No interruption to maintenance screen
- New menu ready when service mode ends

# During Active Orders
- Kiosks with customers mid-order will queue the update
- Update applies after order completes
- Customer won't lose their cart
```

### For Developers
```
# Adding New Menu Event Types

1. Backend: Add event model to SSEEventModels.py
2. Backend: Add to SSEEvent union
3. Frontend: Add type to KioskSSEEvent
4. Frontend: Add handler in useSSEMenuUpdates
5. Test with SSE event simulator
```

---

## Success Criteria

✅ **Functional Requirements:**
- Menu changes broadcast to all kiosks within 1 second
- New media downloads complete within 10 seconds
- UI updates smoothly without crashes
- Works during service mode (silently)
- Handles active orders gracefully

✅ **Performance Requirements:**
- < 1s latency from backend activation to SSE event
- < 10s for media download (10 items average)
- < 100KB memory overhead per kiosk
- No impact on order processing

✅ **Reliability Requirements:**
- 99% success rate for menu changes
- Automatic retry on network failures
- Graceful degradation (keep old menu if update fails)

---

## Summary

This implementation plan provides:

1. ✅ **Complete architecture** - Backend to frontend flow
2. ✅ **Incremental downloads** - Only new items/categories
3. ✅ **Silent mode** - Works during service mode
4. ✅ **Edge cases handled** - Orders, transitions, failures
5. ✅ **No media cleanup** - Keep all menus (Option 1)
6. ✅ **SSE-based** - Uses existing mature infrastructure
7. ✅ **Phased rollout** - MVP → Enhancements
8. ✅ **Well-tested** - Comprehensive test scenarios

**Ready to implement!** 🚀

Start with Phase 1 (Backend SSE event), then Phase 2 (Frontend hook), then Phase 3 (Edge cases).
