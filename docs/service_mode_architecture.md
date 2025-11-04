# Service Mode Architecture Plan

## Overview
Implementation of a service mode feature for kiosk frontend that allows backend to activate/deactivate service mode on multiple kiosks simultaneously. Service mode displays a picture and blocks user interactions, with graceful handling of active orders.

## Architecture Diagram

```mermaid
graph TB
    Admin[Admin Interface] --> API[Service Mode API Endpoint]
    API --> Logic[Service Mode Logic Layer]
    Logic --> DB[(kiosk_service_mode table)]
    Logic --> SSE[SSE Event Bus]
    
    DB --> |Check Active Status| Logic
    SSE --> |Broadcast Events| Kiosk1[Kiosk 001 - Active]
    SSE --> |Broadcast Events| Kiosk2[Kiosk 002 - Active]
    SSE -.-> |Ignore Inactive| Kiosk3[Kiosk 003 - Inactive]
    
    subgraph "Database Schema"
        ServiceTable[kiosk_service_mode<br/>- kiosk_username<br/>- is_service_mode<br/>- service_picture_name<br/>- activated_at<br/>- activated_by]
    end
    
    subgraph "API Request"
        Request[POST /api/kiosk/service-mode<br/>{<br/>  kiosk_usernames: [kiosk_001, kiosk_002],<br/>  is_service_mode: true,<br/>  service_picture_name: maintenance<br/>}]
    end
    
    subgraph "SSE Event"
        Event[KIOSK_SERVICE_MODE_CHANGED<br/>{<br/>  kiosk_username: kiosk_001,<br/>  is_service_mode: true,<br/>  service_picture_name: maintenance<br/>}]
    end
```

## Key Requirements

### Backend Implementation
1. **Database Schema**: Simple `kiosk_service_mode` table tracking service state per kiosk
2. **API Endpoint**: Accepts list of kiosk usernames for batch operations
3. **SSE Broadcasting**: Only send events to active kiosk subscribers
4. **Picture Support**: Store service picture name for frontend display
5. **Audit Trail**: Track activation time and responsible user

### Service Mode Behavior
- **Immediate Blocking**: Block all new user interactions when activated
- **Graceful Orders**: Allow active order-handling to complete before showing service mode
- **Picture Display**: Show specified service picture based on backend configuration
- **Inactive Handling**: Ignore kiosks not currently connected via SSE

### Technical Approach
- Use existing SSE infrastructure for real-time communication
- Leverage current kiosk user management system
- Integrate with existing database migration system
- Follow established patterns for API endpoints and logic layers

## Implementation Scope
**Phase 1 (Current)**: Backend-only implementation
- Database schema and migrations
- API endpoints and logic
- SSE event broadcasting
- Testing and documentation

**Phase 2 (Future)**: Frontend integration
- Service mode overlay component
- State management integration
- Graceful order completion logic
- UI/UX implementation