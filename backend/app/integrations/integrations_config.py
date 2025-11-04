# integrations_config.py
# Clean configuration for external service integrations - URLs, flags, and basic settings only
# Now supports kiosk-specific configurations with fallbacks to global defaults

import os
import logging
from dataclasses import dataclass
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class PaymentConfig:
    """Payment gateway configuration - URLs and settings only"""

    # Mode flag
    mockup_mode: bool = False

    # Production service URLs
    gateway_url: str = ""
    gateway_endpoint: str = ""
    merchant_id: str = ""
    terminal_id: str = ""
    api_key: str = ""
    
    # DC_INPAS specific
    inpas_host: str = ""
    inpas_port: int = 0
    
    # Basic settings
    timeout_seconds: int = 30
    max_retries: int = 3
    use_ssl: bool = True
    
    @classmethod
    def from_env(cls, kiosk_username: Optional[str] = None) -> 'PaymentConfig':
        """Load from environment variables with optional kiosk-specific overrides"""
        # Try to get kiosk-specific configuration first
        if kiosk_username:
            from ..kiosk_configuration_service import get_kiosk_configuration_service
            kiosk_service = get_kiosk_configuration_service()
            pos_terminal_id, pos_config = kiosk_service.get_pos_terminal_config(kiosk_username)
            
            if pos_config:
                # Check for mockup mode from YAML address or environment variable
                is_mockup_from_yaml = pos_config.address == "mockup_mode"
                is_mockup_from_env = os.getenv("PAYMENT_MOCKUP", "false").lower() == "true"
                mockup_mode = is_mockup_from_yaml or is_mockup_from_env
                
                final_gateway_url = pos_config.address if not is_mockup_from_yaml else os.getenv("PAYMENT_GATEWAY_URL", "")
                final_gateway_endpoint = pos_config.endpoint if pos_config.endpoint else os.getenv("PAYMENT_GATEWAY_ENDPOINT", "/mocks/payment")
                
                # Log configuration loading details
                logger.info(f"Payment config loaded for kiosk {kiosk_username}: "
                           f"mockup_mode={mockup_mode} (yaml={is_mockup_from_yaml}, env={is_mockup_from_env}), "
                           f"gateway_url='{final_gateway_url}', endpoint='{final_gateway_endpoint}', terminal_id='{pos_terminal_id}', "
                           f"timeout={pos_config.timeout}s, retries={pos_config.retry_count}")
                
                # Use kiosk-specific settings with environment fallbacks (no hardcoded URLs)
                return cls(
                    mockup_mode=mockup_mode,
                    gateway_url=final_gateway_url,
                    gateway_endpoint=final_gateway_endpoint,
                    merchant_id=os.getenv("PAYMENT_MERCHANT_ID", ""),
                    terminal_id=pos_terminal_id or os.getenv("PAYMENT_TERMINAL_ID", ""),
                    api_key=os.getenv("PAYMENT_API_KEY", ""),
                    inpas_host=os.getenv("INPAS_HOST", ""),
                    inpas_port=int(os.getenv("INPAS_PORT", "0")),
                    timeout_seconds=pos_config.timeout,
                    max_retries=pos_config.retry_count,
                    use_ssl=os.getenv("PAYMENT_USE_SSL", "true").lower() == "true"
                )
        
        # Fall back to global environment variables (no hardcoded defaults)
        global_mockup = os.getenv("PAYMENT_MOCKUP", "false").lower() == "true"
        global_gateway_url = os.getenv("PAYMENT_GATEWAY_URL", "")
        
        logger.info(f"Payment config using global fallback: "
                   f"mockup_mode={global_mockup}, gateway_url='{global_gateway_url}'")
        
        return cls(
            mockup_mode=global_mockup,
            gateway_url=global_gateway_url,
            gateway_endpoint=os.getenv("PAYMENT_GATEWAY_ENDPOINT", "/mocks/payment"),
            merchant_id=os.getenv("PAYMENT_MERCHANT_ID", ""),
            terminal_id=os.getenv("PAYMENT_TERMINAL_ID", ""),
            api_key=os.getenv("PAYMENT_API_KEY", ""),
            inpas_host=os.getenv("INPAS_HOST", ""),
            inpas_port=int(os.getenv("INPAS_PORT", "0")),
            timeout_seconds=int(os.getenv("PAYMENT_TIMEOUT", "30")),
            max_retries=int(os.getenv("PAYMENT_MAX_RETRIES", "3")),
            use_ssl=os.getenv("PAYMENT_USE_SSL", "true").lower() == "true"
        )


@dataclass
class FiscalConfig:
    """Fiscal gateway configuration - URLs and settings only"""

    # Mode flag
    mockup_mode: bool = False

    # Production KKT URLs
    kkt_host: str = ""
    kkt_endpoint: str = ""
    kkt_port: int = 0
    fiscal_number: str = ""
    inn: str = ""
    ofd_provider: str = ""
    
    # Basic settings
    timeout_seconds: int = 20
    max_retries: int = 2
    use_ssl: bool = True
    fiscal_mode: str = "OSN"
    
    @classmethod
    def from_env(cls, kiosk_username: Optional[str] = None) -> 'FiscalConfig':
        """Load from environment variables with optional kiosk-specific overrides"""
        # Try to get kiosk-specific configuration first
        if kiosk_username:
            from ..kiosk_configuration_service import get_kiosk_configuration_service
            kiosk_service = get_kiosk_configuration_service()
            fiscal_device_id, fiscal_config = kiosk_service.get_fiscal_device_config(kiosk_username)
            
            if fiscal_config:
                # Check for mockup mode from YAML address or environment variable
                is_mockup_from_yaml = fiscal_config.address == "mockup_mode"
                is_mockup_from_env = os.getenv("FISCAL_MOCKUP", "false").lower() == "true"
                mockup_mode = is_mockup_from_yaml or is_mockup_from_env
                
                final_kkt_host = fiscal_config.address if not is_mockup_from_yaml else os.getenv("KKT_HOST", "")
                final_kkt_endpoint = fiscal_config.endpoint if fiscal_config.endpoint else os.getenv("KKT_ENDPOINT", "/mocks/fiscal")
                
                # Log configuration loading details
                logger.info(f"Fiscal config loaded for kiosk {kiosk_username}: "
                           f"mockup_mode={mockup_mode} (yaml={is_mockup_from_yaml}, env={is_mockup_from_env}), "
                           f"kkt_host='{final_kkt_host}', endpoint='{final_kkt_endpoint}', device_id='{fiscal_device_id}', "
                           f"timeout={fiscal_config.timeout}s, retries={fiscal_config.retry_count}")
                
                # Use kiosk-specific settings with environment fallbacks (no hardcoded URLs)
                return cls(
                    mockup_mode=mockup_mode,
                    kkt_host=final_kkt_host,
                    kkt_endpoint=final_kkt_endpoint,
                    kkt_port=int(os.getenv("KKT_PORT", "0")),
                    fiscal_number=os.getenv("FISCAL_NUMBER", ""),
                    inn=os.getenv("FISCAL_INN", ""),
                    ofd_provider=os.getenv("OFD_PROVIDER", ""),
                    timeout_seconds=fiscal_config.timeout,
                    max_retries=fiscal_config.retry_count,
                    use_ssl=os.getenv("FISCAL_USE_SSL", "true").lower() == "true",
                    fiscal_mode=os.getenv("FISCAL_MODE", "OSN")
                )
        
        # Fall back to global environment variables (no hardcoded defaults)
        global_mockup = os.getenv("FISCAL_MOCKUP", "false").lower() == "true"
        global_kkt_host = os.getenv("KKT_HOST", "")
        
        logger.info(f"Fiscal config using global fallback: "
                   f"mockup_mode={global_mockup}, kkt_host='{global_kkt_host}'")
        
        return cls(
            mockup_mode=global_mockup,
            kkt_host=global_kkt_host,
            kkt_endpoint=os.getenv("KKT_ENDPOINT", "/mocks/fiscal"),
            kkt_port=int(os.getenv("KKT_PORT", "0")),
            fiscal_number=os.getenv("FISCAL_NUMBER", ""),
            inn=os.getenv("FISCAL_INN", ""),
            ofd_provider=os.getenv("OFD_PROVIDER", ""),
            timeout_seconds=int(os.getenv("FISCAL_TIMEOUT", "20")),
            max_retries=int(os.getenv("FISCAL_MAX_RETRIES", "2")),
            use_ssl=os.getenv("FISCAL_USE_SSL", "true").lower() == "true",
            fiscal_mode=os.getenv("FISCAL_MODE", "OSN")
        )


@dataclass
class KDSConfig:
    """KDS configuration - URLs and settings only"""

    # Mode flag
    mockup_mode: bool = False

    # Production KDS URLs
    kds_api_url: str = ""
    kds_endpoint: str = ""
    kds_api_key: str = ""
    kitchen_station_id: str = ""
    notification_webhook_url: str = ""
    
    # Basic settings
    timeout_seconds: int = 10
    max_retries: int = 2
    use_ssl: bool = True
    auto_confirm_orders: bool = False
    
    @classmethod
    def from_env(cls, kiosk_username: Optional[str] = None) -> 'KDSConfig':
        """Load from environment variables with optional kiosk-specific overrides"""
        # Try to get kiosk-specific configuration first
        if kiosk_username:
            from ..kiosk_configuration_service import get_kiosk_configuration_service
            kiosk_service = get_kiosk_configuration_service()
            kds_name, kds_config = kiosk_service.get_kds_config(kiosk_username)
            
            if kds_config:
                # Check for mockup mode from YAML address or environment variable
                is_mockup_from_yaml = kds_config.address == "mockup_mode"
                is_mockup_from_env = os.getenv("KDS_MOCKUP", "false").lower() == "true"
                mockup_mode = is_mockup_from_yaml or is_mockup_from_env
                
                final_kds_api_url = kds_config.address if not is_mockup_from_yaml else os.getenv("KDS_API_URL", "")
                final_kds_endpoint = kds_config.endpoint if kds_config.endpoint else os.getenv("KDS_ENDPOINT", "/mocks/kds")
                
                # Log configuration loading details
                logger.info(f"KDS config loaded for kiosk {kiosk_username}: "
                           f"mockup_mode={mockup_mode} (yaml={is_mockup_from_yaml}, env={is_mockup_from_env}), "
                           f"kds_api_url='{final_kds_api_url}', endpoint='{final_kds_endpoint}', station_id='{kds_name}', "
                           f"timeout={kds_config.timeout}s, retries={kds_config.retry_count}")
                
                # Use kiosk-specific settings with environment fallbacks (no hardcoded URLs)
                return cls(
                    mockup_mode=mockup_mode,
                    kds_api_url=final_kds_api_url,
                    kds_endpoint=final_kds_endpoint,
                    kds_api_key=os.getenv("KDS_API_KEY", ""),
                    kitchen_station_id=kds_name or os.getenv("KDS_STATION_ID", ""),
                    notification_webhook_url=os.getenv("KDS_WEBHOOK_URL", ""),
                    timeout_seconds=kds_config.timeout,
                    max_retries=kds_config.retry_count,
                    use_ssl=os.getenv("KDS_USE_SSL", "true").lower() == "true",
                    auto_confirm_orders=os.getenv("KDS_AUTO_CONFIRM", "false").lower() == "true"
                )
        
        # Fall back to global environment variables (no hardcoded defaults)
        global_mockup = os.getenv("KDS_MOCKUP", "false").lower() == "true"
        global_kds_api_url = os.getenv("KDS_API_URL", "")
        
        logger.info(f"KDS config using global fallback: "
                   f"mockup_mode={global_mockup}, kds_api_url='{global_kds_api_url}'")
        
        return cls(
            mockup_mode=global_mockup,
            kds_api_url=global_kds_api_url,
            kds_endpoint=os.getenv("KDS_ENDPOINT", "/mocks/kds"),
            kds_api_key=os.getenv("KDS_API_KEY", ""),
            kitchen_station_id=os.getenv("KDS_STATION_ID", ""),
            notification_webhook_url=os.getenv("KDS_WEBHOOK_URL", ""),
            timeout_seconds=int(os.getenv("KDS_TIMEOUT", "10")),
            max_retries=int(os.getenv("KDS_MAX_RETRIES", "2")),
            use_ssl=os.getenv("KDS_USE_SSL", "true").lower() == "true",
            auto_confirm_orders=os.getenv("KDS_AUTO_CONFIRM", "false").lower() == "true"
        )


@dataclass
class PrinterConfig:
    """Printer gateway configuration - settings for receipt printing"""

    # Mode flag
    mockup_mode: bool = True

    # File-based printing settings
    receipts_folder: str = "receipts"
    
    # Real printer settings (for future use)
    printer_host: str = ""
    printer_endpoint: str = ""
    printer_port: int = 0
    printer_model: str = ""
    
    # Basic settings
    timeout_seconds: int = 10
    max_retries: int = 2
    
    @classmethod
    def from_env(cls, kiosk_username: Optional[str] = None) -> 'PrinterConfig':
        """Load from environment variables with optional kiosk-specific overrides"""
        # Try to get kiosk-specific configuration first
        if kiosk_username:
            from ..kiosk_configuration_service import get_kiosk_configuration_service
            kiosk_service = get_kiosk_configuration_service()
            printer_device_id, printer_config = kiosk_service.get_printer_device_config(kiosk_username)
            
            if printer_config:
                # Check for mockup mode from YAML address or environment variable
                is_mockup_from_yaml = printer_config.address == "mockup_mode"
                is_mockup_from_env = os.getenv("PRINTER_MOCKUP", "true").lower() == "true"
                mockup_mode = is_mockup_from_yaml or is_mockup_from_env
                
                final_printer_host = printer_config.address if not is_mockup_from_yaml else os.getenv("PRINTER_HOST", "")
                final_printer_endpoint = printer_config.endpoint if printer_config.endpoint else os.getenv("PRINTER_ENDPOINT", "/mocks/printer")
                
                # Log configuration loading details
                logger.info(f"Printer config loaded for kiosk {kiosk_username}: "
                           f"mockup_mode={mockup_mode} (yaml={is_mockup_from_yaml}, env={is_mockup_from_env}), "
                           f"printer_host='{final_printer_host}', endpoint='{final_printer_endpoint}', device_id='{printer_device_id}', "
                           f"timeout={printer_config.timeout}s, retries={printer_config.retry_count}")
                
                # Single-path policy: resolve receipts folder from kiosk YAML INTEGRATIONS_LOG_BASE_PATH
                receipts_folder_resolved = ""
                try:
                    kiosk_all = kiosk_service.get_kiosk_config(kiosk_username)
                    log_base = None
                    if kiosk_all:
                        for util_conf in [
                            kiosk_all.pos_terminal_config,
                            kiosk_all.fiscal_device_config,
                            kiosk_all.printer_device_config,
                            kiosk_all.kds_config
                        ]:
                            if util_conf and util_conf.additional_settings and "INTEGRATIONS_LOG_BASE_PATH" in util_conf.additional_settings:
                                log_base = util_conf.additional_settings.get("INTEGRATIONS_LOG_BASE_PATH")
                                break
                    if log_base:
                        base_dir = Path(log_base)
                        if base_dir.exists() and base_dir.is_dir() and os.access(str(base_dir), os.W_OK):
                            receipts_folder_resolved = str(base_dir / "DEBUG_receipts")
                        else:
                            logger.warning(f"Printer receipts: base invalid for kiosk {kiosk_username}: {base_dir}; skipping receipts")
                    else:
                        logger.warning(f"Printer receipts: INTEGRATIONS_LOG_BASE_PATH not set for kiosk {kiosk_username}; skipping receipts")
                except Exception:
                    logger.warning(f"Printer receipts: failed to resolve base path for kiosk {kiosk_username}; skipping receipts")

                return cls(
                    mockup_mode=mockup_mode,
                    receipts_folder=receipts_folder_resolved,
                    printer_host=final_printer_host,
                    printer_endpoint=final_printer_endpoint,
                    printer_port=int(os.getenv("PRINTER_PORT", "0")),
                    printer_model=os.getenv("PRINTER_MODEL", ""),
                    timeout_seconds=printer_config.timeout,
                    max_retries=printer_config.retry_count
                )
        
        # Fall back to global environment variables
        global_mockup = os.getenv("PRINTER_MOCKUP", "true").lower() == "true"
        global_printer_host = os.getenv("PRINTER_HOST", "")
        
        logger.info(f"Printer config using global fallback: "
                   f"mockup_mode={global_mockup}, printer_host='{global_printer_host}'")
        
        return cls(
            mockup_mode=global_mockup,
            receipts_folder=os.getenv("RECEIPTS_FOLDER", "app/integrations/DEBUG_receipts"),
            printer_host=global_printer_host,
            printer_endpoint=os.getenv("PRINTER_ENDPOINT", "/mocks/printer"),
            printer_port=int(os.getenv("PRINTER_PORT", "0")),
            printer_model=os.getenv("PRINTER_MODEL", ""),
            timeout_seconds=int(os.getenv("PRINTER_TIMEOUT", "10")),
            max_retries=int(os.getenv("PRINTER_MAX_RETRIES", "2"))
        )


@dataclass
class IntegrationsConfig:
    """Master configuration for all external services"""
    
    payment: PaymentConfig
    fiscal: FiscalConfig
    kds: KDSConfig
    printer: PrinterConfig
    
    # Global settings
    global_timeout: int = 60
    enable_logging: bool = True
    
    @classmethod
    def from_env(cls, kiosk_username: Optional[str] = None) -> 'IntegrationsConfig':
        """Load all configurations from environment with optional kiosk-specific overrides"""
        return cls(
            payment=PaymentConfig.from_env(kiosk_username),
            fiscal=FiscalConfig.from_env(kiosk_username),
            kds=KDSConfig.from_env(kiosk_username),
            printer=PrinterConfig.from_env(kiosk_username),
            global_timeout=int(os.getenv("INTEGRATIONS_TIMEOUT", "60")),
            enable_logging=os.getenv("INTEGRATIONS_LOGGING", "true").lower() == "true"
        )


# Global configuration instance
_config: Optional[IntegrationsConfig] = None


def get_integrations_config(kiosk_username: Optional[str] = None) -> IntegrationsConfig:
    """Get integrations configuration with optional kiosk-specific overrides"""
    if kiosk_username:
        # Return kiosk-specific configuration (not cached globally)
        return IntegrationsConfig.from_env(kiosk_username)
    
    # Use global cached configuration for non-kiosk requests
    global _config
    if _config is None:
        _config = IntegrationsConfig.from_env()
    return _config


def set_integrations_config(config: IntegrationsConfig) -> None:
    """Set global integrations configuration"""
    global _config
    _config = config


# Environment variables documentation for deployment
ENV_VARS_GLOBAL_FALLBACKS = {
    "PAYMENT_GATEWAY_URL": "Global fallback payment gateway URL",
    "KKT_HOST": "Global fallback KKT device URL",
    "KDS_API_URL": "Global fallback kitchen system URL",
    "PRINTER_HOST": "Global fallback printer host"
}

ENV_VARS_OPTIONAL = {
    "PAYMENT_MOCKUP": "true/false - use mockup payment processing",
    "FISCAL_MOCKUP": "true/false - use mockup fiscal processing",
    "KDS_MOCKUP": "true/false - use mockup kitchen processing",
    "PRINTER_MOCKUP": "true/false - use file-based receipt printing",
    "RECEIPTS_FOLDER": "folder path for saving receipt files"
}

# NOTE: Kiosk-specific configurations are now loaded from kiosk_config.yaml
# Each kiosk has its own device addresses, timeouts, and retry settings
KIOSK_CONFIG_STRUCTURE = {
    "kiosk_username": {
        "POS_TERMINAL_ID": "Device identifier for POS terminal",
        "POS_TERMINAL_ADDRESS": "IP:PORT for POS terminal",
        "POS_TERMINAL_TIMEOUT": "Timeout in seconds",
        "POS_TERMINAL_RETRY": "Number of retry attempts",
        "FISCAL_DEVICE_ID": "Device identifier for fiscal device",
        "FISCAL_DEVICE_ADDRESS": "IP:PORT for fiscal device",
        "FISCAL_DEVICE_TIMEOUT": "Timeout in seconds",
        "FISCAL_DEVICE_RETRY": "Number of retry attempts",
        "PRINTER_DEVICE_ID": "Device identifier for printer",
        "PRINTER_DEVICE_ADDRESS": "IP:PORT for printer",
        "PRINTER_DEVICE_TIMEOUT": "Timeout in seconds",
        "PRINTER_DEVICE_RETRY": "Number of retry attempts",
        "KDS_NAME": "Kitchen station name/identifier",
        "KDS_ADDRESS": "IP:PORT for KDS",
        "KDS_TIMEOUT": "Timeout in seconds",
        "KDS_RETRY": "Number of retry attempts"
    }
}