# KIOSK CATEGORIES DATA FLOW - COMPLETE ANALYSIS

## Overview
This document traces the complete data flow for categories from the FastAPI backend through Server-Sent Events (SSE) to the React frontend, including initial login, menu updates, and SSE-driven refreshes.

---

## PART 1: BACKEND ENDPOINTS

### 1.1 Categories Endpoints

#### Endpoint 1: `/api/v1/kiosk/categories` (GET)
**File:** `backend/app/api/KioskCategoriesEndpoint.py`

```python
@router.get(
    "/categories",
    response_model=KioskCategoriesListResponse,
    status_code=status.HTTP_200_OK,
)
async def get_categories_for_kiosk(
    current_user: User = Depends(get_current_kiosk_user),
    db: Session = Depends(get_db)
)
```

**Purpose:** Fetch all food categories for the active menu

**Authentication:** Requires kiosk user JWT token

**Response Model:** `KioskCategoriesListResponse`
- `categories[]`: Array of category objects with:
  - `name`: Category name
  - `created_at`: Creation timestamp
  - `display_order`: Display order in menu (ordered by backend)
- `total_count`: Number of categories

**Business Logic File:** `backend/app/logic/KioskCategoriesLogic.py`
- Fetches categories from active menu
- Validates user is active
- Returns categories ordered by `display_order`
- Returns empty list if no active menu exists

#### Endpoint 2: `/api/v1/kiosk/menu/all-for-preload` (GET)
**File:** `backend/app/api/AllItemsAndCategoriesFromMenuForPreloadEndpoint.py`

```python
@router.get(
    "/menu/all-for-preload",
    response_model=AllItemsAndCategoriesFromMenuForPreloadResponse,
    status_code=status.HTTP_200_OK,
)
async def get_all_items_and_categories_from_menu_for_preload(
    current_user: User = Depends(get_current_kiosk_user),
    db: Session = Depends(get_db)
)
```

**Purpose:** Fetch ALL item IDs and category names from active menu for media preloading

**Key Feature:** Returns items/categories regardless of:
- Stock quantity (includes items with stock = 0)
- Availability status
- Active/archived status

**Response Model:** `AllItemsAndCategoriesFromMenuForPreloadResponse`
- `item_ids[]`: All item IDs in active menu
- `category_names[]`: All category names in active menu
- Returns empty lists if no active menu exists

**Use Case:** Called at login to cache media for items that might become available during the session via SSE updates

---

### 1.2 Authentication Endpoint (Returns Initial User Data)

#### Endpoint: `/api/v1/kiosk/login` (POST)
**File:** `backend/app/api/KioskAuthenticationEndpoints.py`

**Purpose:** Kiosk authentication

**Request Model:** `KioskLoginRequest`
- `username`: Kiosk username
- `password`: Kiosk password

**Response Model:** `LoginResponse`
- `access_token`: JWT token for subsequent requests
- `token_type`: "bearer"
- `expires_in`: Token expiration in seconds
- `user`: User object with:
  - `user_id`
  - `username`
  - `email`
  - `role_name`
  - `is_active`

**Note:** Categories are NOT returned in login response. Frontend fetches categories separately after login.

---

### 1.3 SSE Events Endpoint

#### Endpoint: `/api/v1/kiosk/events` (GET with WebSocket-like streaming)
**File:** `backend/app/api/events_sse.py`

**Purpose:** Long-lived SSE connection for real-time event streaming

**Authentication:** JWT token passed as query parameter `?token=<JWT>`

**Event Types Related to Categories:**
1. **MENU_ACTIVATED** - When menu changes
   - `menu_id`: New menu ID
   - `menu_name`: New menu name
   - Triggers complete menu refresh (categories + items)

2. **ITEM_CREATED** - New item added to menu
   - `item_id`, `name_ru`, `name_eng`, `description`, `price`, `stock`, `food_category_name`
   - NEW items might trigger category visibility changes

3. **ITEM_STATUS_CHANGED** - Item active/inactive (stop list)
   - `item_id`, `is_active`

4. **ITEM_STOCK_CHANGED** - Item stock updated
   - `item_id`, `stock_quantity`, `change_quantity`
   - Items with stock=0 might be hidden; stock>0 makes them visible

5. **HEARTBEAT** - Connection keep-alive
   - Sent every 15 seconds to prevent timeout

**Backend Event Emission:** Managed by `backend/app/websockets/event_bus.py`
- Events broadcast to `"kiosk_broadcast"` channel
- All connected kiosks receive all events
- Frontend filters events by type

---

## PART 2: FRONTEND API CALLS

### 2.1 API Transport Layer

**File:** `frontend/apps/kiosk/src/api/categoriesApi.ts`

```typescript
export async function getCategories(): Promise<CategoriesListResponseDto> {
  const response = await fetchWithAuth(KIOSK_CATEGORIES, {
    method: 'GET',
    retryOnUnauthenticated: true,
  });
  return handleApiResponse<CategoriesListResponseDto>(response);
}
```

**Constants:** `frontend/apps/kiosk/src/config/constants.ts`
- `KIOSK_CATEGORIES = '/kiosk/categories'`
- `KIOSK_MENU_ALL_FOR_PRELOAD = '/kiosk/menu/all-for-preload'`
- `API_BASE_URL = '/api'` (proxied to `/api/v1`)

**HTTP Client:** `frontend/apps/kiosk/src/api/apiHttpClient.ts`
- `fetchWithAuth()`: Adds Authorization header with JWT
- Automatic token refresh on 401
- Handles errors and retries

**API Functions:**

1. **getCategories()** - Fetch categories from `/api/kiosk/categories`
   - Called by services to fetch categories
   - Returns raw DTO from backend

2. **getAllMenuItemsForPreload()** - Fetch preload data from `/api/kiosk/menu/all-for-preload`
   - Called at login and during menu changes
   - Returns: `{ item_ids: number[], category_names: string[] }`

---

### 2.2 Service Layer (Business Logic)

**File:** `frontend/apps/kiosk/src/services/categories.service.ts`

**Functions:**

1. **fetchCategoriesAndGetDomain()** - DTO → Domain mapping
   - Calls `getCategories()` from API layer
   - Maps DTO to Domain model
   - Returns: `CategoriesList` domain object

2. **fetchCategoriesAndGetVM()** - DTO → Domain → ViewModel
   - Calls `fetchCategoriesAndGetDomain()`
   - Maps Domain to ViewModel
   - Returns: `CategoriesListVM` for UI consumption

3. **fetchCategoriesWithNavigationAndGetVM()** - Enhanced ViewModel with synthetic "NEW" category
   - Fetches categories from backend
   - Prepends synthetic "NEW" category (created by frontend, not backend)
   - Adds display names: `[1] New!`, `[2] Category1`, `[3] Category2`, etc.
   - Sorts by `display_order` from backend
   - Returns: Enhanced `CategoriesListVM`

**Data Transformation:**
- Backend `display_order` field is preserved
- Frontend adds synthetic navigation numbering
- Categories ordered by backend-provided `display_order`

---

### 2.3 Context Layer (State Management)

**File:** `frontend/apps/kiosk/src/contexts/CategoriesContext.tsx`

```typescript
export const CategoriesProvider = ({ children }: { children: ReactNode }) => {
  // Persisted state with localStorage (24-hour TTL)
  const [categoriesData, setCategoriesData] = usePersistedState<CategoriesListVM>(
    'kiosk_categories',
    { categories: [], totalCount: 0, isLoading: false, error: null },
    PERSISTENCE_CONFIGS.CATEGORIES
  )

  // Fetch categories and update state
  const fetchCategories = useCallback(async () => {
    setCategoriesData(createLoadingCategoriesVM())
    try {
      const categoriesVM = await fetchCategoriesWithNavigationAndGetVM()
      setCategoriesData(categoriesVM)
    } catch (error) {
      setCategoriesData(createErrorCategoriesVM(errorMessage))
    }
  }, [])

  // Auto-fetch on mount
  useEffect(() => {
    fetchCategories()
  }, [fetchCategories])

  return (
    <CategoriesContext.Provider value={{ categoriesData, categories, fetchCategories, clearError }}>
      {children}
    </CategoriesContext.Provider>
  )
}
```

**Context Value:**
- `categoriesData`: Full ViewModel with metadata
- `categories`: Array of CategoryVM objects
- `isLoading`: Loading state
- `error`: Error message
- `fetchCategories()`: Manual refetch function
- `clearError()`: Clear error state

**Persistence:**
- Categories stored in localStorage as `'kiosk_categories'`
- 24-hour TTL (survives page reload)
- Synced with IndexedDB media cache

**Consumer Hook:**
```typescript
const { categories, fetchCategories, error } = useCategories()
```

---

## PART 3: SSE (SERVER-SENT EVENTS) MECHANISMS

### 3.1 SSE Service (Low-level Event Management)

**File:** `frontend/apps/kiosk/src/SSESubscription/sseService.ts`

**Class:** `SSEService`

**Connection Lifecycle:**

1. **connect()** - Establish SSE connection
   - Retrieves access token (or refreshes it if expired)
   - Creates EventSource with token as query param: `?token=<JWT>`
   - Subscribes to backend `"kiosk_broadcast"` channel
   - Starts heartbeat monitoring (20-second timeout)
   - Auto-reconnects on failure with exponential backoff

2. **disconnect()** - Close SSE connection
   - Called on logout
   - Clears emergency mode flag
   - Stops heartbeat monitoring

3. **onEvent(eventType, handler)** - Register event handler
   - Each component can subscribe to specific event types
   - Multiple handlers can be registered per event type

**Reconnection Strategy:**

- **Phase 1 (Attempts 1-4):** Exponential backoff (2s → 4s → 8s → 16s) = ~30s total
- **Phase 2 (Attempts 5+):** Slow polling every 60 seconds forever
- **Emergency Mode:** Persisted to localStorage, survives page refresh
- **Auto-recovery:** When connection restored, exits emergency mode

**Token Refresh on Connection Failure:**
- When SSE connection fails, attempts to refresh access token before reconnecting
- Handles backend restart scenario where in-memory tokens invalidated

**Event Handlers:**

1. **onmessage** - Process incoming SSE event
   - Parses JSON payload
   - Updates last message time for heartbeat monitoring
   - Routes to specific event handlers

2. **onerror** - Handle connection errors
   - Closes stale EventSource immediately
   - Attempts token refresh
   - Schedules reconnection with backoff

3. **Heartbeat Monitoring:**
   - Backend sends HEARTBEAT event every 15 seconds
   - Frontend checks for messages every 5 seconds
   - If no message for 20 seconds, considers connection dead
   - Forces reconnection attempt

**SSE Event Types (from backend):**

```typescript
type KioskSSEEvent = 
  | ItemStatusChangedEvent       // ITEM_STATUS_CHANGED
  | ItemPromotionChangedEvent    // ITEM_PROMOTION_CHANGED
  | ItemStockChangedEvent        // ITEM_STOCK_CHANGED
  | ItemCreatedEvent             // ITEM_CREATED (includes food_category_name)
  | ItemPropertiesChangedEvent   // ITEM_PROPERTIES_CHANGED
  | OrderStatusChangedEvent      // ORDER_STATUS_CHANGED
  | OrderEventTriggeredEvent     // ORDER_EVENT_TRIGGERED
  | KioskServiceModeChangedEvent // KIOSK_SERVICE_MODE_CHANGED
  | MenuActivatedEvent           // MENU_ACTIVATED (triggers full refresh)
  | HeartbeatEvent               // HEARTBEAT (keep-alive)
```

---

### 3.2 SSE Menu Update Hook

**File:** `frontend/apps/kiosk/src/SSESubscription/useSSEMenuUpdates.ts`

**Purpose:** Listen for menu activation events and trigger menu refresh

```typescript
export function useSSEMenuUpdates({ onMenuActivated }: UseSSEMenuUpdatesProps) {
  useEffect(() => {
    // Register handler for MENU_ACTIVATED events
    sseService.onEvent('MENU_ACTIVATED', handleSSEEvent)
  }, [handleSSEEvent])

  const handleSSEEvent = useCallback((event: KioskSSEEvent) => {
    if (event.event_type !== 'MENU_ACTIVATED') return
    const menuEvent = event as MenuActivatedEvent
    onMenuActivated(menuEvent.menu_id, menuEvent.menu_name)
  }, [onMenuActivated])
}
```

**Event Payload:**
- `event_type`: "MENU_ACTIVATED"
- `menu_id`: ID of activated menu
- `menu_name`: Name of activated menu

**Trigger:** Menu change on backend or admin switches menu

---

### 3.3 Menu Refresh Event Bridge (High-level Integration)

**File:** `frontend/apps/kiosk/src/components/MenuRefreshEventBridge.tsx`

**Purpose:** Orchestrate complete menu refresh when MENU_ACTIVATED event arrives

**Flow When Menu Changes:**

1. **Clear Cart:** Items from old menu no longer valid
   ```typescript
   clearCart()
   ```

2. **Defer on Order Processing:** If customer in middle of payment/receipt
   - Defers activation until customer leaves `/order-handling` page
   - Prevents UI disruption during critical operation

3. **Download New Media:**
   ```typescript
   const result = await menuRefreshService.handleMenuActivation(
     menuId,
     menuName,
     (progress) => setDownloadProgress(progress)
   )
   ```
   - Incremental download (skips already cached items)
   - Only downloads media for new menu

4. **Refresh Categories Context:**
   ```typescript
   await fetchCategories()
   ```
   - Calls `GET /api/kiosk/categories` for new menu
   - Updates CategoriesContext with new categories

5. **Refresh Items Context:**
   ```typescript
   await refetchItems()
   ```
   - Fetches available items from new menu

6. **Navigate to Main Screen:**
   ```typescript
   navigate('/main')
   ```
   - Unless on `/service-mode` page (silent refresh)

**Special Handling:**

- **Service Mode:** Downloads media silently in background, no UI overlay shown
- **Emergency Mode Recovery:** When SSE connection restored after outage, auto-refetch all categories and items

---

### 3.4 SSE Item Update Hook

**File:** `frontend/apps/kiosk/src/SSESubscription/useSSEItemUpdates.ts`

**Purpose:** Listen for item updates and notify ItemsContext

**Event Types Handled:**

1. **ITEM_STATUS_CHANGED** - Item added to stop list
   ```typescript
   { itemId, isAvailable: event.is_active }
   ```

2. **ITEM_PROMOTION_CHANGED** - Item promotion status changed
   ```typescript
   { itemId, promoted: event.promoted }
   ```

3. **ITEM_STOCK_CHANGED** - Stock replenished/depleted
   ```typescript
   { itemId, stockQuantity, isAvailable: stockQuantity > 0 }
   ```

4. **ITEM_CREATED** - New item created (may have new category)
   ```typescript
   { itemId, newItem: true, foodCategory, priceNetKopecks, ... }
   ```

5. **ITEM_PROPERTIES_CHANGED** - Item details updated
   ```typescript
   { itemId, nameRu, priceNetKopecks, ... }
   ```

**Impact on Categories:**
- New items (`ITEM_CREATED`) include `food_category_name`
- Frontend doesn't auto-create categories (backend controls categories)
- Categories updated via `MENU_ACTIVATED` event (triggers full refresh)

---

## PART 4: DATA FLOW DIAGRAM

### Login Flow (Initial Categories Load)

```
1. User enters credentials on Login.tsx
   ↓
2. AuthContext.login(credentials)
   ↓
3. POST /api/v1/kiosk/login
   ← Returns: { access_token, user, ... }
   ↓
4. Token stored in localStorage
   ↓
5. CategoriesProvider auto-mounts and calls fetchCategories()
   ↓
6. Categories.service.fetchCategoriesWithNavigationAndGetVM()
   ↓
7. GET /api/v1/kiosk/categories
   ← Returns: { categories[{ name, display_order, created_at }], total_count }
   ↓
8. DTO → Domain → ViewModel transformation
   ↓
9. Add synthetic [NEW] category, number categories for navigation
   ↓
10. CategoriesContext.setState(categoriesVM)
    ↓
11. UI renders categories from context
    ↓
12. SSEService.connect() establishes SSE connection with token
    ↓
13. SSE subscriptions registered (MENU_ACTIVATED, ITEM_CREATED, etc.)
```

### Media Preload at Login

```
1. Login.tsx: handleSubmit()
   ↓
2. GET /api/v1/kiosk/menu/all-for-preload
   ← Returns: { item_ids[], category_names[] }
   ↓
3. Add synthetic 'NEW' category to category_names
   ↓
4. mediaCacheService.downloadAllMedia(categoryNames, itemIds)
   ↓
5. Download all media to IndexedDB (background, shows progress bar)
   ↓
6. Navigate to /main (or /service-mode)
```

### Menu Change Flow (Via SSE MENU_ACTIVATED)

```
Backend Admin Action:
  Activates a new menu
  ↓
Backend Event:
  Publishes MENU_ACTIVATED event to kiosk_broadcast
  ↓
SSE Stream:
  Server sends: { event_type: "MENU_ACTIVATED", menu_id, menu_name }
  ↓
Frontend - sseService:
  Receives SSE event, routes to registered handlers
  ↓
Frontend - MenuRefreshEventBridge:
  Receives MENU_ACTIVATED event via useSSEMenuUpdates hook
  ↓
  1. Check if safe to activate (not in order processing)
  2. If deferred, wait for order completion
  ↓
  3. clearCart()
  4. GET /api/v1/kiosk/menu/all-for-preload
     ← New menu's categories and items
  5. mediaCacheService.downloadAllMedia(newCategories, newItems)
     (Incremental - skips already cached)
  6. await fetchCategories()
     GET /api/v1/kiosk/categories
     ← Categories from new active menu
     CategoriesContext updates
  7. await refetchItems()
     GET /api/v1/kiosk/items/available
     ← Items from new active menu
     ItemsContext updates
  8. navigate('/main')
```

### Categories Refresh on Server Recovery (SSE Emergency Mode Exit)

```
Scenario: Server was down, connection lost, Emergency Mode activated
  ↓
Server comes back online
  ↓
Frontend attempts to reconnect (backoff + slow polling)
  ↓
SSE connection succeeds
  ↓
Frontend detects: wasInEmergencyMode && !isEmergencyMode
  ↓
MenuRefreshEventBridge effect:
  1. await fetchCategories()
  2. await refetchItems()
  ↓
Categories and items refreshed (may have changed while server down)
```

### SSE Item Update Flow (Non-Menu Changes)

```
Backend Event (e.g., stock replenished):
  Publishes ITEM_STOCK_CHANGED: { item_id, stock_quantity }
  ↓
SSE Stream:
  Server sends event to all connected kiosks
  ↓
Frontend - useSSEItemUpdates:
  Receives event, calls onItemUpdate({ itemId, stockQuantity, ... })
  ↓
Frontend - ItemsContext:
  Updates item in local state (may show/hide item)
  ↓
UI Updates:
  Item grid refreshes to show updated availability
  ↓
Categories:
  No direct update (categories only change via MENU_ACTIVATED)
  Items context handles visibility
```

---

## PART 5: STORAGE & CACHING

### Frontend Storage Layers

1. **Token Storage** (`localStorage`)
   - `access_token`: JWT for API requests
   - `refresh_token`: JWT for token refresh

2. **Session Persistence** (`localStorage`)
   - `kiosk_session`: Persisted user and session data
   - TTL: Refreshed on token refresh

3. **Categories Persistence** (`localStorage`)
   - Key: `'kiosk_categories'`
   - Value: `CategoriesListVM` (full ViewModel)
   - TTL: 24 hours

4. **Media Cache** (`IndexedDB`)
   - Stores binary media files (images, videos)
   - Keys: `category_<name>`, `item_<id>`, etc.
   - Persists across page reloads and sessions

5. **Emergency Mode Flag** (`localStorage`)
   - Key: `'kiosk_emergency_mode'`
   - Value: `'true'` if in emergency mode
   - Survives page refresh and restart

### Cache Invalidation

- **Login:** Clear all media cache, preload new media
- **Menu Activation:** Incremental media download (skip cached), refresh categories + items
- **Page Refresh During Emergency:** Restore emergency flag from localStorage, attempt SSE reconnect
- **Logout:** Clear all tokens, media cache, and emergency flag

---

## PART 6: ERROR HANDLING & EDGE CASES

### Network Failures

**SSE Connection Lost:**
- Phase 1: Aggressive exponential backoff (2s, 4s, 8s, 16s)
- Phase 2: Slow polling every 60 seconds forever
- Emergency Mode: Activated after ~30 seconds of no connection
- Recovery: Auto-exits emergency when connection restored

**API Errors (Categories Fetch):**
- 401 Unauthorized: Triggers automatic token refresh, retries
- 500 Server Error: Cached categories shown to user
- Network Error: Uses persisted categories from localStorage

### Concurrent Requests

**Race Condition Prevention:**
- `isConnecting` flag in SSEService prevents duplicate connection attempts
- `performMenuActivation` deferred while order processing active
- `setCategoriesData` is atomic state update

### Edge Cases

1. **Page Refresh During Emergency Mode:**
   - Emergency flag persisted in localStorage
   - Page reload immediately shows emergency overlay
   - Attempts to reconnect with existing refresh token

2. **New Category Added via ITEM_CREATED:**
   - Item creation event includes `food_category_name`
   - If category is new, users won't see it until MENU_ACTIVATED event
   - Frontend doesn't auto-create categories (backend manages categories)

3. **Menu Activation During Order Processing:**
   - Activation deferred until order completes
   - User doesn't experience disruption mid-payment
   - Activation triggered when leaving `/order-handling` page

4. **Token Expiration During SSE:**
   - Heartbeat timeout (20 seconds) triggers reconnection
   - Reconnection attempts token refresh before connecting
   - If token refresh fails, waits for next backoff attempt

5. **Service Mode:**
   - Menu activation downloads media silently (no UI overlay)
   - Items and categories refreshed but no navigation
   - Allows background sync while display shows service mode

---

## PART 7: KEY FILES SUMMARY

### Backend Files

| File | Purpose |
|------|---------|
| `api/KioskCategoriesEndpoint.py` | GET /kiosk/categories endpoint |
| `api/AllItemsAndCategoriesFromMenuForPreloadEndpoint.py` | GET /kiosk/menu/all-for-preload endpoint |
| `api/events_sse.py` | SSE stream endpoint |
| `logic/KioskCategoriesLogic.py` | Categories business logic |
| `models/SSEEventModels.py` | SSE event Pydantic models |
| `websockets/event_bus.py` | Event broadcasting (not file-based) |

### Frontend Files - API/Transport Layer

| File | Purpose |
|------|---------|
| `api/categoriesApi.ts` | GET /kiosk/categories transport call |
| `api/getAllMenuItemsForPreload.api.ts` | GET /kiosk/menu/all-for-preload transport call |
| `api/apiHttpClient.ts` | HTTP client with auth, token refresh |
| `config/constants.ts` | API endpoint constants |

### Frontend Files - Service Layer

| File | Purpose |
|------|---------|
| `services/categories.service.ts` | DTO→Domain→ViewModel transformation |
| `services/menuRefresh.service.ts` | Menu activation handling |
| `services/mediaCache.service.ts` | Media download and caching |
| `services/auth.service.ts` | Login/logout business logic |

### Frontend Files - Context Layer

| File | Purpose |
|------|---------|
| `contexts/CategoriesContext.tsx` | Categories state management |
| `contexts/ItemsContext.tsx` | Items state management |
| `contexts/AuthContext.tsx` | Authentication state management |

### Frontend Files - SSE Layer

| File | Purpose |
|------|---------|
| `SSESubscription/sseService.ts` | SSE connection and event routing |
| `SSESubscription/useSSEMenuUpdates.ts` | Listen for MENU_ACTIVATED events |
| `SSESubscription/useSSEItemUpdates.ts` | Listen for item update events |

### Frontend Files - Components

| File | Purpose |
|------|---------|
| `components/MenuRefreshEventBridge.tsx` | Orchestrate menu change flow |
| `pages/Login.tsx` | Login and media preload |

---

## PART 8: IMPORTANT NOTES

### Categories in Login Response
- **NOT included** in login response from backend
- Fetched separately via GET /kiosk/categories
- Allows login to complete quickly while categories load

### Synthetic "NEW" Category
- **Created by frontend**, not backend
- Always first in category list
- Navigation display: `[1] New!`
- No media files for "NEW" category

### Display Order
- Provided by backend in categories response
- Used to order categories in UI
- Frontend preserves this ordering
- Each category can have custom order value

### Categories vs Items
- **Categories** change only via MENU_ACTIVATED event (menu switch)
- **Items** change via ITEM_CREATED, ITEM_STOCK_CHANGED, ITEM_STATUS_CHANGED, etc.
- Item updates don't affect visible categories (categories are stable)
- New items belong to existing categories

### Media Preload Strategy
- **At Login:** Fetch ALL items and categories from active menu
- **Includes items with stock=0** (may be replenished during session)
- **Incremental Download:** During menu change, only download NEW media
- **Purpose:** Ensure media available for items that become visible via SSE updates

### SSE Token Authentication
- EventSource doesn't support custom headers
- Token passed as query parameter: `?token=<JWT>`
- Token refreshed on connection failure before reconnecting
- Handles backend restart scenario

### Emergency Mode
- Persisted to localStorage
- Survives page refresh and browser restart
- Exits automatically when connection restored
- Enables "server went down" overlay in UI

---

## SUMMARY TABLE

| Component | Initial Load | Menu Change | SSE Updates | Storage |
|-----------|-------------|------------|------------|---------|
| **Categories** | GET /categories | MENU_ACTIVATED → GET /categories | No direct update | localStorage |
| **Items** | GET /items/available | MENU_ACTIVATED → GET /items/available | ITEM_STOCK_CHANGED, ITEM_STATUS_CHANGED, ITEM_CREATED, ITEM_PROPERTIES_CHANGED | Context only |
| **Media** | Preload all at login | Incremental download on MENU_ACTIVATED | MEDIA_UPDATE event (silent background update) | IndexedDB |
| **Token** | Login POST → token | Refresh on 401 | Refresh on SSE error | localStorage |
| **Emergency Flag** | N/A | N/A | Set on max reconnect attempts, cleared on recovery | localStorage |

---

## CRITICAL DATA FLOW POINTS

1. **Login Flow:**
   - Credentials → POST /kiosk/login → Token + User
   - Token → GET /categories → Categories
   - Token → GET /menu/all-for-preload → Media list
   - Token → SSE /events → Real-time updates

2. **Menu Change Flow:**
   - Backend → MENU_ACTIVATED SSE event
   - Frontend → Clear cart, GET /menu/all-for-preload
   - Frontend → GET /categories (for new menu)
   - Frontend → GET /items/available (for new menu)
   - Frontend → Download media + refresh UI

3. **Categories Source:**
   - Always from active menu (filtered in backend)
   - Display order controlled by backend
   - Frontend adds synthetic "NEW" category for UI navigation
   - Persisted to localStorage for offline/reload support

4. **Categories Update Trigger:**
   - MENU_ACTIVATED SSE event (menu switched)
   - Manual refetch (logout/login flow)
   - Page reload (from localStorage)
   - Server recovery (connection restored from emergency)

---

## END OF ANALYSIS

This document covers:
- All backend endpoints involved in categories data flow
- All frontend API functions for fetching categories
- SSE event types and their impact on categories
- Complete data transformation pipeline (DTO→Domain→ViewModel)
- Storage and caching mechanisms
- Error handling and edge cases
- Integration points and orchestration

All data flows have been traced from backend endpoints through to frontend rendering.

