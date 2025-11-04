# Kiosk App Architecture Rules

This document outlines the architectural principles and guidelines for the Zero Culture Kiosk frontend application.

## Directory Structure

```
/src
  /api           # Backend API calls (transport layer only)
  /components    # Reusable UI components
  /config        # Configuration and constants
  /contexts      # React contexts (Auth, etc.)
  /hooks         # Custom React hooks (thin wrappers over services)
  /models        # Data models (DTO, Domain, ViewModel)
    /dto         # Data Transfer Objects (API shape)
    /domain      # Business domain models
    /view        # View models (UI-optimized)
  /pages         # Route pages (Login, MainScreen, etc.)
  /services      # Business logic, orchestration
    /mappers     # Pure mapping functions (DTO ↔ Domain ↔ ViewModel)
  /stores        # State management (Zustand for cart, orders)
  /types         # TypeScript type definitions
  /utils         # Utilities, formatters, validators
```

## Layered Architecture

### 1. Data Flow Layers

**API Layer** (`/api`)
- Transport-only functions
- Returns DTOs matching backend JSON shape
- No business logic
- Example: `authApi.ts`, `ordersApi.ts`

**DTO Layer** (`/models/dto`)
- Exact backend API response/request shapes
- Source of truth: Backend OpenAPI/Swagger
- Snake_case naming (matches backend)
- Example: `LoginResponseDto`, `OrderItemDto`

**Domain Layer** (`/models/domain`)
- Clean business entities
- CamelCase naming
- Independent of transport and UI concerns
- Example: `User`, `Order`, `MenuItem`

**ViewModel Layer** (`/models/view`)
- UI-optimized data structures
- Formatted strings, computed fields
- Example: `UserVM`, `OrderVM`, `MenuItemVM`

**Service Layer** (`/services`)
- Business logic orchestration
- Calls API functions
- Uses mappers for DTO → Domain → ViewModel
- Example: `auth.service.ts`, `orders.service.ts`

**Mapper Layer** (`/services/mappers`)
- Pure transformation functions
- No side effects, no I/O
- Example: `mapLoginResponseDtoToDomainSession()`

### 2. Responsibilities by Layer

**Pages** (`/pages`)
- Assemble screen layout
- Call hooks for data
- Work only with ViewModels
- No direct API calls

**Components** (`/components`)
- Presentational, reusable
- Receive props (ViewModels)
- No business logic

**Hooks** (`/hooks`)
- Thin wrappers over services
- Return ViewModels or Domain models
- Example: `useAuth()`, `useOrders()`

**Contexts** (`/contexts`)
- Global state (user session, etc.)
- Delegate logic to services
- Example: `AuthContext`

**Stores** (`/stores`)
- Client-side state (cart, selected items)
- Use Zustand for reactive state
- Do NOT cache server data here

**Utils** (`/utils`)
- Pure functions
- Formatters, validators, storage helpers
- Example: `formatPrice()`, `storage.ts`

## Naming Conventions

- **API files**: `feature.api.ts` → `getOrders()`, `createOrder()`
- **DTOs**: `feature.dto.ts` → `OrderDto`, `CreateOrderDto`
- **Domain**: `feature.ts` → `Order`, `MenuItem`
- **ViewModels**: `feature.vm.ts` → `OrderVM`, `MenuItemVM`
- **Services**: `feature.service.ts` → `getOrdersFormatted()`
- **Mappers**: `feature.mappers.ts` → `mapOrderDtoToDomain()`
- **Hooks**: `useFeature.ts` → `useOrders()`
- **Components**: `ComponentName.tsx` (PascalCase)
- **Exports**: Named exports only (no default exports)

## Authentication

- Kiosk-specific endpoints: `/api/kiosk/auth/login`, `/api/kiosk/auth/refresh`
- Access token stored in memory
- Refresh token in HttpOnly cookie
- Session persisted to `localStorage` with expiry (`kiosk_app_session` key)
- Route protection via `RouteGuard` component

## Styling

- **Tailwind CSS 4.1.3** with REM-based spacing
- Custom screens: `mq900` (max-width: 900px), `mq450` (max-width: 450px)
- Fonts: PT Sans (Locofy components), DM Sans (Login page)
- Preflight disabled (`preflight: false` in tailwind.config.js)

## Component Architecture

### From Locofy (MainScreen)
- `Cart.tsx` - Shopping cart sidebar
- `CartItem.tsx` - Individual cart item
- `CategoryItem.tsx` - Category navigation
- `DividersVertical.tsx` - Visual separator
- `Item.tsx` - Product card
- `ItemList.tsx` - Product list container

### Custom Components
- `Login.tsx` - Authentication page
- `RouteGuard.tsx` - Protected route wrapper
- `MainScreen.tsx` - Main kiosk interface

## State Management

- **Server State**: Categories and Items via React Context + hooks
- **Client State**: Zustand stores for cart, order flow, navigation state
- **Auth State**: React Context + localStorage persistence
- **Navigation State**: Zustand store for active category, item selection, keyboard navigation

## Error Handling

- Centralized `ApiError` class with types: `network`, `unauthorized`, `server`, `unknown`
- UI displays user-friendly error messages
- 401 handling: Auto-refresh token → retry request

## Future Enhancements

1. **Menu Data**: Fetch categories and items from backend
2. **Cart State**: Zustand store for cart management
3. **Order Placement**: Full order flow with payment integration
4. **Real-time Updates**: SSE/WebSocket for order status
5. **TanStack Query**: Server state caching and synchronization

## Key Principles

1. **Separation of Concerns**: Each layer has a single responsibility
2. **Type Safety**: TypeScript everywhere, strict mode enabled
3. **No Leaky Abstractions**: API details never reach UI layer
4. **Testability**: Pure functions, dependency injection
5. **Consistency**: Follow established patterns across features
6. **Performance**: Code splitting, lazy loading (future)

---

*This architecture mirrors the admin app for consistency while tailoring to kiosk-specific needs.*
