 (return # CATEGORIES DATA FLOW - QUICK REFERENCE GUIDE

## At a Glance

### Backend Endpoints
```
POST   /api/v1/kiosk/login                           → Get access token
GET    /api/v1/kiosk/categories                      → Get categories (main endpoint)
GET    /api/v1/kiosk/menu/all-for-preload           → Get item IDs + category names (for preload)
GET    /api/v1/kiosk/events?token=<JWT>             → SSE stream (long-lived)
```

### Frontend API Functions
```
login(credentials)                                   → /api/v1/kiosk/login
getCategories()                                      → /api/v1/kiosk/categories
getAllMenuItemsForPreload()                          → /api/v1/kiosk/menu/all-for-preload
sseService.connect()                                 → /api/v1/kiosk/events
```

### Frontend Service Functions
```
fetchCategoriesAndGetDomain()      → DTO → Domain
fetchCategoriesAndGetVM()          → DTO → Domain → ViewModel
fetchCategoriesWithNavigationAndGetVM()  → Enhanced ViewModel (with synthetic "NEW")
```

### Frontend Context
```
useCategories() → { categories, fetchCategories, error, isLoading }
```

### SSE Event Types (Categories-Related)
```
MENU_ACTIVATED          → Menu changed → Full refresh
ITEM_CREATED            → New item → May show/hide categories
ITEM_STOCK_CHANGED      → Stock updated → Item visibility changes
ITEM_STATUS_CHANGED     → Stop list → Item visibility changes
HEARTBEAT               → Keep-alive (15 seconds)
```

---

## Login Flow - 3 Steps

```
STEP 1: Authenticate
  User submits credentials
  POST /api/v1/kiosk/login
  ← { access_token, user, expires_in }
  Token saved to localStorage

STEP 2: Download Media
  GET /api/v1/kiosk/menu/all-for-preload
  ← { item_ids: [], category_names: [] }
  Download all media to IndexedDB
  (Shows progress bar)

STEP 3: Initialize App
  CategoriesProvider mounts
  GET /api/v1/kiosk/categories
  ← { categories: [], total_count }
  Store in localStorage (24h TTL)
  SSEService.connect()
  Navigate to /main
```

---

## Menu Change Flow - 5 Steps

```
Backend Admin switches menu
  ↓
SSE Event: MENU_ACTIVATED
  ↓
STEP 1: Check Safety
  If order processing → defer until customer leaves

STEP 2: Clear Old Data
  clearCart()
  
STEP 3: Download New Media
  GET /api/v1/kiosk/menu/all-for-preload
  Download incrementally (skip cached)

STEP 4: Refresh Data
  GET /api/v1/kiosk/categories (new menu)
  GET /api/v1/kiosk/items/available (new menu)

STEP 5: Navigate
  navigate('/main')
```

---

## Categories Storage Locations

| Location | Key | Duration | Purpose |
|----------|-----|----------|---------|
| localStorage | 'kiosk_categories' | 24 hours | Persist categories across page reload |
| React Context | CategoriesContext | Session | Real-time updates via fetches/SSE |
| IndexedDB | category_<name> | Persistent | Store media files (not category data) |

---

## Critical Paths

### Path 1: Initial Load
```
Login → POST /login → GET /categories → Store localStorage → SSE connect
```

### Path 2: Menu Changes
```
MENU_ACTIVATED SSE → GET /menu/all-for-preload → GET /categories → localStorage update
```

### Path 3: Server Recovery
```
Connection restored from emergency → MenuRefreshEventBridge → GET /categories + GET /items
```

### Path 4: Page Reload
```
Page refresh → AuthContext init → GET /categories (or use localStorage) → SSE reconnect
```

---

## Component Hierarchy

```
App
├── AuthProvider
│   ├── Manages login/logout
│   └── Triggers SSE connection
├── CategoriesProvider
│   ├── Fetches categories on mount
│   └── Exposes useCategories() hook
├── ItemsProvider
│   ├── Fetches items on mount
│   └── Listens to SSE item updates
└── MenuRefreshEventBridge
    └── Listens to MENU_ACTIVATED SSE
        └── Orchestrates menu change flow
```

---

## File Map (Quick Find)

### Backend Categories
```
api/KioskCategoriesEndpoint.py              → GET /kiosk/categories
logic/KioskCategoriesLogic.py               → Business logic
services/KioskCategoriesDBCRUD.py           → Database queries
```

### Backend SSE
```
api/events_sse.py                           → SSE endpoint
models/SSEEventModels.py                    → Event definitions
websockets/event_bus.py                     → Event broadcasting
```

### Frontend API
```
api/categoriesApi.ts                        → getCategories() call
api/getAllMenuItemsForPreload.api.ts         → getAllMenuItemsForPreload() call
config/constants.ts                         → Endpoint URLs
```

### Frontend Services
```
services/categories.service.ts              → Data transformations
services/menuRefresh.service.ts             → Menu change handling
services/mediaCache.service.ts              → Media download/cache
```

### Frontend Contexts & Hooks
```
contexts/CategoriesContext.tsx              → State management
contexts/ItemsContext.tsx                   → Items state
contexts/AuthContext.tsx                    → Auth state
```

### Frontend SSE
```
SSESubscription/sseService.ts               → Connection management
SSESubscription/useSSEMenuUpdates.ts        → Menu change listener
SSESubscription/useSSEItemUpdates.ts        → Item update listener
```

### Frontend Components
```
components/MenuRefreshEventBridge.tsx       → Orchestrates menu changes
pages/Login.tsx                             → Login & media preload
```

---

## Key Implementation Details

### Categories NOT in Login Response
- Login returns: `{ access_token, user }`
- Categories fetched separately after login
- This allows login to complete quickly

### Synthetic "NEW" Category
- Created by frontend, not backend
- Always displayed first
- No media files for "NEW"
- Navigation numbering: [1] New!, [2] Category1, etc.

### Display Order
- Backend provides `display_order` field
- Frontend preserves this ordering
- Used for UI ordering, not business logic

### SSE Token Authentication
- EventSource doesn't support custom headers
- Token passed as query parameter: `?token=<JWT>`
- Token refreshed on error before reconnecting

### Emergency Mode
- Activated after ~30s of no SSE connection
- Persisted to localStorage
- Survives page refresh/restart
- Automatically cleared on reconnection

### Categories Update Triggers
1. Manual refetch (user action)
2. Login/logout flow
3. MENU_ACTIVATED SSE event
4. Page reload (from localStorage)
5. Server recovery from outage

---

## Common Queries

**Q: Where does a category first come from?**
A: Backend `GET /api/v1/kiosk/categories` endpoint, filtered by active menu.

**Q: How are categories ordered?**
A: By `display_order` field from backend. Frontend adds numeric navigation prefix ([1], [2], etc.).

**Q: When do categories refresh?**
A: On login, menu change (MENU_ACTIVATED SSE), page reload, or server recovery.

**Q: Do categories update when items change?**
A: No. Items update independently via SSE. Categories only change when menu changes (MENU_ACTIVATED).

**Q: What if a new item is created with a new category name?**
A: Backend controls category creation. Frontend won't show new category until MENU_ACTIVATED event.

**Q: Where are categories stored?**
A: React Context (active) + localStorage (backup for reload) + IndexedDB (media files only).

**Q: Can user see categories offline?**
A: Yes, from localStorage cache (24-hour TTL).

**Q: What happens if SSE dies for 30+ seconds?**
A: Emergency Mode activated. Kiosk shows "server down" overlay but continues with cached data.

---

## Troubleshooting

| Symptom | Cause | Solution |
|---------|-------|----------|
| Categories don't load | No active menu | Create/activate a menu in admin |
| Categories not updating | SSE event not received | Check SSE connection, check event_bus |
| Old categories show after menu change | localStorage not cleared | Check cache invalidation logic |
| Categories stuck in loading | API error | Check network, check auth token |
| Categories missing on page reload | localStorage expired | Check TTL settings |

---

## Performance Considerations

- Categories fetched once per session (except menu changes)
- Stored in localStorage to avoid refetch on page reload
- SSE keeps data fresh without repeated polls
- Media preload includes all categories for offline availability
- Incremental media download on menu change (skip cached items)

---

## Security Notes

- Categories filtered by active menu (backend enforces)
- Access requires valid kiosk JWT token
- Token auto-refreshed on 401 errors
- SSE token passed as query param (no custom headers supported by EventSource)
- Refresh token stored in HttpOnly cookie (more secure than localStorage)

---

END OF QUICK REFERENCE
