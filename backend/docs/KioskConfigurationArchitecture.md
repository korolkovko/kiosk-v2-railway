# KioskConfigurationArchitecture.md
# Kiosk Configuration Architecture Documentation

## Overview

The kiosk configuration system provides a hierarchical approach to managing device-specific settings for multiple kiosks. Each kiosk user (e.g., `kiosk_001`, `kiosk_002`) has its own configuration section with specific device addresses, timeouts, and retry settings.

## Architecture Components

### 1. Configuration Files

#### `kiosk_config.yaml`
- **Location**: `backend/app/kiosk_config.yaml`
- **Purpose**: Hierarchical configuration for all kiosk users
- **Format**: YAML with kiosk username as top-level keys

```yaml
kiosk_001:
  POS_TERMINAL_ID: POS_001
  POS_TERMINAL_ADDRESS: 192.168.1.100:8080
  POS_TERMINAL_TIMEOUT: 45
  POS_TERMINAL_RETRY: 5
  
  FISCAL_DEVICE_ID: FISCAL_001
  FISCAL_DEVICE_ADDRESS: 192.168.1.101:9090
  FISCAL_DEVICE_TIMEOUT: 25
  FISCAL_DEVICE_RETRY: 3
  
  PRINTER_DEVICE_ID: PRINTER_001
  PRINTER_DEVICE_ADDRESS: 192.168.1.102:515
  PRINTER_DEVICE_TIMEOUT: 15
  PRINTER_DEVICE_RETRY: 2
  
  KDS_NAME: Kitchen_Station_A
  KDS_ADDRESS: 192.168.1.103:3000
  KDS_TIMEOUT: 20
  KDS_RETRY: 3
```

#### `.env` file
- **Purpose**: Global fallback settings and application configuration
- **Usage**: Fallback when kiosk-specific settings are not available

### 2. Service Layer

#### `KioskConfigurationService`
- **Location**: `backend/app/kiosk_configuration_service.py`
- **Purpose**: Load, cache, and resolve kiosk-specific configurations
- **Features**:
  - LRU caching for performance
  - Configuration validation
  - Fallback mechanism
  - Hot-reload capability

#### Key Methods:
- `get_kiosk_config(kiosk_username)`: Get complete kiosk configuration
- `get_pos_terminal_config(kiosk_username)`: Get POS terminal settings
- `get_fiscal_device_config(kiosk_username)`: Get fiscal device settings
- `get_printer_device_config(kiosk_username)`: Get printer settings
- `get_kds_config(kiosk_username)`: Get KDS settings
- `validate_kiosk_config(kiosk_username)`: Validate configuration
- `refresh_cache()`: Refresh configuration cache

### 3. Integration Layer

#### Updated Integration Configs
All integration configuration classes now support kiosk-specific overrides:

- `PaymentConfig.from_env(kiosk_username)`
- `FiscalConfig.from_env(kiosk_username)`
- `KDSConfig.from_env(kiosk_username)`
- `PrinterConfig.from_env(kiosk_username)`

#### Configuration Priority:
1. **Kiosk-specific settings** (from `kiosk_config.yaml`)
2. **Global environment variables** (from `.env`)
3. **Default values** (hardcoded in dataclasses)

### 4. FSM Integration

#### FSM State Handler Updates
- **Location**: `backend/app/orchestrator/fsm_state_handler.py`
- **Changes**: 
  - Loads `KioskConfigurationService` in `__init__`
  - Resolves kiosk-specific timeouts for each operation
  - Logs device usage for audit trail
  - Passes kiosk context to integration gateways

#### Key Integration Points:
- `_handle_init_state()`: Uses kiosk-specific fiscal device settings
- `_handle_awaiting_payment_state()`: Uses kiosk-specific POS terminal settings
- `_handle_receipt_printing()`: Uses kiosk-specific printer settings
- `_handle_kds_integration()`: Uses kiosk-specific KDS settings

## Configuration Flow

```
Order Processing Request
         ↓
FSM State Handler (has kiosk_username)
         ↓
KioskConfigurationService.get_*_config(kiosk_username)
         ↓
kiosk_config.yaml lookup
         ↓
Integration Gateway with kiosk-specific settings
```

## Benefits

1. **Performance**: Configuration cached, not read for each order
2. **Flexibility**: Each kiosk can have different device addresses/settings
3. **Maintainability**: Clear hierarchical structure in YAML
4. **Fallback Safety**: Global defaults when kiosk config missing
5. **Hot-Reload**: Configuration changes without application restart
6. **Validation**: Built-in configuration validation and error reporting

## Usage Examples

### Adding a New Kiosk
1. Add new section to `kiosk_config.yaml`:
```yaml
kiosk_003:
  POS_TERMINAL_ID: POS_003
  POS_TERMINAL_ADDRESS: 192.168.1.300:8080
  # ... other device configurations
```

2. Call `refresh_cache()` or restart application

### Validating Configuration
```python
from app.kiosk_configuration_service import get_kiosk_configuration_service

service = get_kiosk_configuration_service()
validation = service.validate_kiosk_config('kiosk_001')

if not validation['valid']:
    print("Configuration issues:", validation['issues'])
```

### Getting Device Configuration
```python
# In FSM State Handler
pos_terminal_id, pos_config = self.kiosk_config_service.get_pos_terminal_config(kiosk_username)

if pos_config:
    timeout = pos_config.timeout
    address = pos_config.address
    retry_count = pos_config.retry_count
```

## Migration Notes

- **Backward Compatibility**: Existing global environment variables still work as fallbacks
- **No Breaking Changes**: Current integrations continue to function
- **Gradual Migration**: Kiosk-specific configs can be added incrementally

## Security Considerations

- Configuration file should be secured in production
- Sensitive data (API keys, credentials) remain in environment variables
- Device addresses and network settings in YAML for easy management