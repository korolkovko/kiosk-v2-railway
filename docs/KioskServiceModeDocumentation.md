# Kiosk Service Mode Documentation

## Overview

The Kiosk Service Mode feature allows administrators to remotely activate/deactivate service mode on multiple kiosks simultaneously. When service mode is activated, kiosks display a service picture and block user interactions. This is useful for maintenance, cleaning, or technical issues.

## Architecture

### Database Schema

#### `kiosk_service_mode` Table

```sql
CREATE TABLE kiosk_service_mode (
    service_mode_id INTEGER PRIMARY KEY,
    kiosk_username VARCHAR(100) NOT NULL UNIQUE REFERENCES users(username) ON DELETE CASCADE,
    is_service_mode BOOLEAN NOT NULL DEFAULT FALSE,
    service_picture_name VARCHAR(100) NULL
);

-- Indexes
CREATE UNIQUE INDEX idx_kiosk_service_mode_username ON kiosk_service_mode(kiosk_username);
CREATE INDEX idx_kiosk_service_mode_status ON kiosk_service_mode(is_service_mode);
```

**Fields:**
- `service_mode_id`: Primary key
- `kiosk_username`: Foreign key to users table (kiosk users only)
- `is_service_mode`: Boolean flag indicating if kiosk is in service mode
- `service_picture_name`: Name of service picture to display (cleared when deactivated)

### SSE Event Model

#### `KIOSK_SERVICE_MODE_CHANGED` Event

```json
{
  "event_type": "KIOSK_SERVICE_MODE_CHANGED",
  "kiosk_username": "kiosk_001",
  "is_service_mode": true,
  "service_picture_name": "maintenance",
  "timestamp": "2025-10-25T19:45:00.000Z"
}
```

## API Endpoints

### Base URL: `/api/v1/kiosk/service-mode`

**Admin Endpoints** (require **admin** or **superadmin** role authentication):
- All management and monitoring endpoints

**Kiosk Self-Service Endpoints** (require **kiosk** authentication):
- Endpoints for kiosks to check their own status

### 1. Get All Service Mode Statuses

**GET** `/status`

Retrieve service mode status for all kiosks.

**Response:**
```json
{
  "kiosks": [
    {
      "kiosk_username": "kiosk_001",
      "is_service_mode": true,
      "service_picture_name": "maintenance",
      "is_kiosk_active": true,
      "has_active_sse_connection": true
    }
  ],
  "total_kiosks": 5,
  "active_kiosks": 4,
  "kiosks_in_service_mode": 2
}
```

### 2. Get Service Mode Status for Specific Kiosk

**GET** `/kiosk-status-for-admin-user/{kiosk_username}`

Retrieve service mode status for a specific kiosk.

**Response:**
```json
{
  "kiosk_username": "kiosk_001",
  "is_service_mode": true,
  "service_picture_name": "maintenance",
  "is_kiosk_active": true,
  "has_active_sse_connection": true
}
```

### 3. Activate Service Mode

**POST** `/activate?kiosk_usernames=kiosk_001&kiosk_usernames=kiosk_002&service_picture_name=maintenance`

Activate service mode on multiple kiosks. **Automatically sends SSE events** to notify kiosks.

### 4. Deactivate Service Mode

**POST** `/deactivate?kiosk_usernames=kiosk_001&kiosk_usernames=kiosk_002`

Deactivate service mode on multiple kiosks. **Automatically sends SSE events** to notify kiosks.

### 5. Get My Service Mode Status (Kiosk Self-Service)

**GET** `/kiosk-status-for-kiosk-user`

**Authentication:** Requires kiosk user authentication (not admin)

Allows kiosk users to check their own service mode status. This is the **canonical endpoint** that kiosks should use to determine if they should display the service mode screen.

**Response:**
```json
{
  "kiosk_username": "kiosk_001",
  "is_service_mode": true,
  "service_picture_name": "maintenance",
  "message": "Kiosk is in service mode"
}
```

**Use Cases:**
- Check service mode status on kiosk login/startup
- Periodic status checks for service mode changes
- Determine which service picture to display
- Fallback check if SSE connection is lost

## Service Mode Behavior

### Activation Process

1. **API Call**: Admin calls service mode API with list of kiosk usernames
2. **Validation**: System validates kiosk usernames exist and are active
3. **Database Update**: Service mode status updated in database
4. **SSE Broadcasting**: Events sent to active kiosk SSE connections
5. **Frontend Response**: Kiosks receive events and activate service mode

### Deactivation Process

1. **API Call**: Admin calls service mode API to deactivate
2. **Database Update**: Service mode status set to false, picture name cleared
3. **SSE Broadcasting**: Events sent to active kiosk SSE connections
4. **Frontend Response**: Kiosks receive events and return to normal operation

### Graceful Order Handling

- **New Orders**: Blocked immediately when service mode activated
- **Active Orders**: Allowed to complete if on order-handling page
- **Order Completion**: Service mode screen shown after order processing finishes

### Error Handling

- **Inactive Kiosks**: Ignored without error (status: "ignored")
- **Non-existent Kiosks**: Ignored without error (status: "ignored")
- **SSE Connection Issues**: Service mode still updated in database
- **Partial Failures**: Individual kiosk errors don't affect others

## Implementation Details

### File Structure

```
backend/app/
├── alembic/versions/create_kiosk_service_mode_table.py  # Database migration
├── api/KioskServiceModeEndpoint.py                     # API endpoints
├── logic/KioskServiceModeLogic.py                      # Business logic
├── services/KioskServiceModeDBCRUD.py                  # Database operations
├── models/KioskServiceModePydanticModel.py             # Request/response models
├── models/SSEEventModels.py                            # SSE event models (updated)
└── database/models.py                                  # SQLAlchemy models (updated)
```

### Key Components

1. **Database Layer**: SQLAlchemy models and CRUD operations
2. **Business Logic**: Transaction management and validation
3. **API Layer**: FastAPI endpoints with authentication
4. **SSE Integration**: Real-time event broadcasting
5. **Error Handling**: Comprehensive error handling and logging

### Security

- **Authentication**: Requires admin or superadmin role
- **Authorization**: Role-based access control
- **Input Validation**: Pydantic models validate all inputs
- **SQL Injection Protection**: SQLAlchemy ORM prevents SQL injection

### Performance Considerations

- **Bulk Operations**: Single API call can update multiple kiosks
- **Database Transactions**: Atomic operations with rollback on failure
- **SSE Filtering**: Events only sent to active subscribers
- **Connection Checking**: Inactive kiosks ignored to avoid timeouts

## Usage Examples

### Activate Service Mode for Maintenance

```bash
curl -X POST "http://localhost:8000/api/v1/kiosk/service-mode/activate?kiosk_usernames=kiosk_001&kiosk_usernames=kiosk_002&service_picture_name=maintenance" \
  -H "Authorization: Bearer <admin_token>"
```

### Deactivate Service Mode

```bash
curl -X POST "http://localhost:8000/api/v1/kiosk/service-mode/deactivate?kiosk_usernames=kiosk_001&kiosk_usernames=kiosk_002" \
  -H "Authorization: Bearer <admin_token>"
```

### Check Service Mode Status

```bash
curl -X GET "http://localhost:8000/api/v1/kiosk/service-mode/status" \
  -H "Authorization: Bearer <admin_token>"
```

## Future Enhancements

1. **Scheduled Service Mode**: Automatic activation/deactivation based on schedules
2. **Service Mode Templates**: Predefined service mode configurations
3. **Notification Integration**: Email/SMS notifications when service mode activated
4. **Audit Logging**: Detailed logs of who activated/deactivated service mode
5. **Frontend Admin Panel**: Web interface for service mode management
6. **Mobile App Integration**: Mobile app for remote service mode control

## Troubleshooting

### Common Issues

1. **Kiosk Not Responding**: Check SSE connection status
2. **Service Mode Not Activating**: Verify kiosk username exists and is active
3. **Permission Denied**: Ensure user has admin or superadmin role
4. **Database Errors**: Check database connection and migration status

### Debugging

1. **Check Logs**: Review application logs for error messages
2. **Verify SSE**: Confirm kiosk has active SSE connection
3. **Database Query**: Check service mode status directly in database
4. **API Testing**: Use curl or Postman to test API endpoints

### Monitoring

1. **Service Mode Statistics**: Use `/status` endpoint for overview
2. **Individual Kiosk Status**: Use `/kiosk-status-for-admin-user/{kiosk_username}` for details
3. **SSE Connection Health**: Monitor SSE connection status
4. **Database Health**: Monitor database performance and connections