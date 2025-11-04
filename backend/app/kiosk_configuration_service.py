# kiosk_configuration_service.py
# Service for resolving kiosk-specific device configurations with caching
# Provides kiosk-specific device IDs and utility-specific settings from YAML config

import os
import yaml
from typing import Optional, Dict, Any
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class KioskUtilityConfig:
    """Configuration for a specific utility (payment, fiscal, printer, KDS) for a kiosk"""
    address: str
    timeout: int
    retry_count: int
    endpoint: str = ""
    additional_settings: Dict[str, Any] = None

    def __post_init__(self):
        if self.additional_settings is None:
            self.additional_settings = {}


@dataclass
class KioskIntegrationsConfig:
    """Complete integration configuration for a specific kiosk"""
    kiosk_username: str
    pos_terminal_id: Optional[str] = None
    pos_terminal_config: Optional[KioskUtilityConfig] = None
    fiscal_device_id: Optional[str] = None
    fiscal_device_config: Optional[KioskUtilityConfig] = None
    printer_device_id: Optional[str] = None
    printer_device_config: Optional[KioskUtilityConfig] = None
    kds_name: Optional[str] = None
    kds_config: Optional[KioskUtilityConfig] = None


class KioskConfigurationService:
    """
    Service for resolving kiosk-specific device configurations.
    Uses caching to avoid reading YAML file for each order.
    
    Configuration Structure (YAML):
    kiosk_001:
      POS_TERMINAL_ID: POS_001
      POS_TERMINAL_ADDRESS: 192.168.1.100:8080
      POS_TERMINAL_TIMEOUT: 45
      POS_TERMINAL_RETRY: 5
      ...
    """
    
    def __init__(self, config_file_path: Optional[str] = None):
        if config_file_path is None:
            # Default to kiosk_config.yaml in the same directory as this file
            config_file_path = Path(__file__).parent / "kiosk_config.yaml"
        
        self.config_file_path = Path(config_file_path)
        self._config_cache: Dict[str, KioskIntegrationsConfig] = {}
        self._cache_initialized = False
        self._config_data: Dict[str, Any] = {}
        
    def _load_yaml_config(self):
        """Load configuration from YAML file"""
        try:
            if not self.config_file_path.exists():
                logger.warning(f"Kiosk configuration file not found: {self.config_file_path}")
                return {}
                
            with open(self.config_file_path, 'r', encoding='utf-8') as file:
                config_data = yaml.safe_load(file) or {}
                logger.info(f"Loaded kiosk configuration from {self.config_file_path}")
                return config_data
                
        except Exception as e:
            logger.error(f"Failed to load kiosk configuration from {self.config_file_path}: {e}")
            return {}
        
    def _initialize_cache(self):
        """Initialize configuration cache by loading YAML file"""
        if self._cache_initialized:
            return
            
        logger.info("Initializing kiosk configuration cache...")
        
        # Load YAML configuration
        self._config_data = self._load_yaml_config()
        
        # Process each kiosk configuration
        for kiosk_username, kiosk_config in self._config_data.items():
            try:
                config = self._load_kiosk_config(kiosk_username, kiosk_config)
                self._config_cache[kiosk_username] = config
                logger.info(f"Loaded configuration for kiosk {kiosk_username}")
            except Exception as e:
                logger.error(f"Failed to load configuration for kiosk {kiosk_username}: {e}")
        
        self._cache_initialized = True
        logger.info(f"Configuration cache initialized for {len(self._config_cache)} kiosks")
    
    def _load_kiosk_config(self, kiosk_username: str, kiosk_config: Dict[str, Any]) -> KioskIntegrationsConfig:
        """Load configuration for a specific kiosk from YAML data"""
        
        # Load POS Terminal configuration
        pos_terminal_id, pos_terminal_config = self._load_utility_config(
            kiosk_config, 'POS_TERMINAL', {'timeout': 30, 'retry_count': 3}
        )
        
        # Load Fiscal Device configuration
        fiscal_device_id, fiscal_device_config = self._load_utility_config(
            kiosk_config, 'FISCAL_DEVICE', {'timeout': 20, 'retry_count': 2}
        )
        
        # Load Printer Device configuration
        printer_device_id, printer_device_config = self._load_utility_config(
            kiosk_config, 'PRINTER_DEVICE', {'timeout': 10, 'retry_count': 2}
        )
        
        # Load KDS configuration (special case with name)
        kds_name, kds_config = self._load_utility_config(
            kiosk_config, 'KDS', {'timeout': 10, 'retry_count': 2}, use_name_instead_of_id=True
        )
        
        return KioskIntegrationsConfig(
            kiosk_username=kiosk_username,
            pos_terminal_id=pos_terminal_id,
            pos_terminal_config=pos_terminal_config,
            fiscal_device_id=fiscal_device_id,
            fiscal_device_config=fiscal_device_config,
            printer_device_id=printer_device_id,
            printer_device_config=printer_device_config,
            kds_name=kds_name,
            kds_config=kds_config
        )
    
    def _load_utility_config(self, kiosk_config: Dict[str, Any], utility_type: str, defaults: Dict[str, Any], use_name_instead_of_id: bool = False) -> tuple[Optional[str], Optional[KioskUtilityConfig]]:
        """Load utility configuration for a specific utility type from YAML data"""
        
        # Check for device ID/name and address
        if use_name_instead_of_id:
            device_key = f"{utility_type}_NAME"
        else:
            device_key = f"{utility_type}_ID"
            
        address_key = f"{utility_type}_ADDRESS"
        endpoint_key = f"{utility_type}_ENDPOINT"
        
        device_identifier = kiosk_config.get(device_key)
        address = kiosk_config.get(address_key)
        endpoint = kiosk_config.get(endpoint_key, "")
        
        # If no configuration found, return None
        if not device_identifier and not address:
            return None, None
        
        # Load timeout and retry settings with fallbacks
        timeout_key = f"{utility_type}_TIMEOUT"
        retry_key = f"{utility_type}_RETRY"
        
        timeout = int(kiosk_config.get(timeout_key, defaults.get('timeout', 30)))
        retry_count = int(kiosk_config.get(retry_key, defaults.get('retry_count', 3)))
        
        # Load additional settings (like EXTERNAL_CALL_DOCUMENTATION)
        additional_settings = {}
        for key, value in kiosk_config.items():
            if key not in [device_key, address_key, endpoint_key, timeout_key, retry_key]:
                additional_settings[key] = value
        
        # Create utility config
        utility_config = KioskUtilityConfig(
            address=address or "",
            endpoint=endpoint,
            timeout=timeout,
            retry_count=retry_count,
            additional_settings=additional_settings
        )
        
        return device_identifier, utility_config
    
    @lru_cache(maxsize=128)
    def get_kiosk_config(self, kiosk_username: str) -> Optional[KioskIntegrationsConfig]:
        """
        Get configuration for a specific kiosk.
        Uses LRU cache for performance optimization.
        """
        self._initialize_cache()
        
        # Use the exact kiosk username as provided (e.g., "kiosk_001")
        return self._config_cache.get(kiosk_username)
    
    def get_pos_terminal_config(self, kiosk_username: str) -> tuple[Optional[str], Optional[KioskUtilityConfig]]:
        """Get POS terminal ID and configuration for a kiosk"""
        config = self.get_kiosk_config(kiosk_username)
        if config:
            return config.pos_terminal_id, config.pos_terminal_config
        return None, None
    
    def get_fiscal_device_config(self, kiosk_username: str) -> tuple[Optional[str], Optional[KioskUtilityConfig]]:
        """Get fiscal device ID and configuration for a kiosk"""
        config = self.get_kiosk_config(kiosk_username)
        if config:
            return config.fiscal_device_id, config.fiscal_device_config
        return None, None
    
    def get_printer_device_config(self, kiosk_username: str) -> tuple[Optional[str], Optional[KioskUtilityConfig]]:
        """Get printer device ID and configuration for a kiosk"""
        config = self.get_kiosk_config(kiosk_username)
        if config:
            return config.printer_device_id, config.printer_device_config
        return None, None
    
    def get_kds_config(self, kiosk_username: str) -> tuple[Optional[str], Optional[KioskUtilityConfig]]:
        """Get KDS name and configuration for a kiosk"""
        config = self.get_kiosk_config(kiosk_username)
        if config:
            return config.kds_name, config.kds_config
        return None, None
    
    def refresh_cache(self):
        """Refresh the configuration cache (useful for runtime config updates)"""
        logger.info("Refreshing kiosk configuration cache...")
        self._config_cache.clear()
        self.get_kiosk_config.cache_clear()
        self._cache_initialized = False
        self._config_data = {}
        self._initialize_cache()
    
    def get_all_configured_kiosks(self) -> list[str]:
        """Get list of all configured kiosk usernames"""
        self._initialize_cache()
        return list(self._config_cache.keys())
    
    def validate_kiosk_config(self, kiosk_username: str) -> Dict[str, Any]:
        """
        Validate kiosk configuration and return validation results.
        Returns dict with validation status and any issues found.
        """
        config = self.get_kiosk_config(kiosk_username)
        
        if not config:
            return {
                'valid': False,
                'issues': [f'No configuration found for kiosk {kiosk_username}'],
                'config_summary': {}
            }
        
        issues = []
        warnings = []
        
        # Validate POS terminal
        if config.pos_terminal_config:
            if not config.pos_terminal_config.address:
                issues.append(f'POS terminal address not configured for kiosk {kiosk_username}')
            if config.pos_terminal_config.timeout <= 0:
                issues.append(f'Invalid POS terminal timeout for kiosk {kiosk_username}')
            if config.pos_terminal_config.retry_count <= 0:
                warnings.append(f'POS terminal retry count is 0 for kiosk {kiosk_username}')
        
        # Validate fiscal device
        if config.fiscal_device_config:
            if not config.fiscal_device_config.address:
                issues.append(f'Fiscal device address not configured for kiosk {kiosk_username}')
            if config.fiscal_device_config.timeout <= 0:
                issues.append(f'Invalid fiscal device timeout for kiosk {kiosk_username}')
            if config.fiscal_device_config.retry_count <= 0:
                warnings.append(f'Fiscal device retry count is 0 for kiosk {kiosk_username}')
        
        # Validate printer
        if config.printer_device_config:
            if not config.printer_device_config.address:
                issues.append(f'Printer device address not configured for kiosk {kiosk_username}')
            if config.printer_device_config.timeout <= 0:
                issues.append(f'Invalid printer device timeout for kiosk {kiosk_username}')
            if config.printer_device_config.retry_count <= 0:
                warnings.append(f'Printer device retry count is 0 for kiosk {kiosk_username}')
        
        # Validate KDS
        if config.kds_config:
            if not config.kds_config.address:
                issues.append(f'KDS address not configured for kiosk {kiosk_username}')
            if config.kds_config.timeout <= 0:
                issues.append(f'Invalid KDS timeout for kiosk {kiosk_username}')
            if config.kds_config.retry_count <= 0:
                warnings.append(f'KDS retry count is 0 for kiosk {kiosk_username}')
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'config_summary': {
                'pos_terminal_id': config.pos_terminal_id,
                'fiscal_device_id': config.fiscal_device_id,
                'printer_device_id': config.printer_device_id,
                'kds_name': config.kds_name,
                'has_pos_config': config.pos_terminal_config is not None,
                'has_fiscal_config': config.fiscal_device_config is not None,
                'has_printer_config': config.printer_device_config is not None,
                'has_kds_config': config.kds_config is not None
            }
        }

    def validate_all_kiosks(self) -> Dict[str, Any]:
        """Validate configurations for all configured kiosks"""
        self._initialize_cache()
        
        results = {}
        overall_valid = True
        
        for kiosk_username in self.get_all_configured_kiosks():
            validation_result = self.validate_kiosk_config(kiosk_username)
            results[kiosk_username] = validation_result
            
            if not validation_result['valid']:
                overall_valid = False
        
        return {
            'overall_valid': overall_valid,
            'kiosk_results': results,
            'total_kiosks': len(results)
        }


# Global service instance
_kiosk_config_service: Optional[KioskConfigurationService] = None


def get_kiosk_configuration_service() -> KioskConfigurationService:
    """Get global kiosk configuration service instance"""
    global _kiosk_config_service
    if _kiosk_config_service is None:
        _kiosk_config_service = KioskConfigurationService()
    return _kiosk_config_service