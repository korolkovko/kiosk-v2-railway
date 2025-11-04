# external_call_documenter.py
# Utility for documenting external API calls with curl-equivalent commands
# Provides debugging and API documentation capabilities for integration layer
# Single-path policy:
# - Per kiosk YAML key INTEGRATIONS_LOG_BASE_PATH controls BOTH external call docs and receipts location
# - If base path missing/invalid/not writable: skip writing and log a short message
# - Do NOT create base directory; only create subfolders under existing base
# External call documentation substructure under base:
#   DEBUG_ExternalCallDocumented/kiosk_{username}/{service}_calls/*.md

import os
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Single-path policy key name (per-kiosk YAML additional setting)
EXTERNAL_LOG_BASE_KEY = "INTEGRATIONS_LOG_BASE_PATH"


def _get_kiosk_additional_setting(kiosk_username: str, key: str) -> Optional[Any]:
    """Fetch a value from kiosk YAML additional_settings across any utility config."""
    try:
        from ..kiosk_configuration_service import get_kiosk_configuration_service

        kiosk_service = get_kiosk_configuration_service()
        kiosk_config = kiosk_service.get_kiosk_config(kiosk_username)
        if kiosk_config:
            utility_configs = [
                kiosk_config.pos_terminal_config,
                kiosk_config.fiscal_device_config,
                kiosk_config.printer_device_config,
                kiosk_config.kds_config
            ]
            for utility_config in utility_configs:
                if utility_config and utility_config.additional_settings:
                    if key in utility_config.additional_settings:
                        return utility_config.additional_settings.get(key)
    except Exception as _e:
        # Do not break flow if configuration cannot be read
        pass
    return None


class ExternalCallDocumenter:
    """
    Utility class for documenting external API calls.
    Generates curl-equivalent commands and saves detailed call logs.
    """
    
    def __init__(self, base_documentation_path: Optional[str] = None):
        """
        Base path is resolved per kiosk from YAML via INTEGRATIONS_LOG_BASE_PATH.
        This parameter is kept for backward compatibility but is not used unless explicitly set.
        """
        self.base_path = Path(base_documentation_path) if base_documentation_path else None
        # IMPORTANT: Do NOT create base directories here. If base path is invalid/missing, we skip later.
    
    def ensure_documentation_directory_exists(self):
        """Create the base documentation directory if it doesn't exist"""
        try:
            self.base_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"External call documentation directory ensured: {self.base_path}")
        except Exception as e:
            logger.error(f"Failed to create documentation directory {self.base_path}: {e}")
    
    def should_document_calls(self, kiosk_username: str) -> bool:
        """
        Check if call documentation is enabled for a specific kiosk.
        Reads from kiosk configuration to determine if documentation should be generated.
        """
        try:
            from ..kiosk_configuration_service import get_kiosk_configuration_service
            
            kiosk_service = get_kiosk_configuration_service()
            kiosk_config = kiosk_service.get_kiosk_config(kiosk_username)
            
            if kiosk_config:
                # Check for EXTERNAL_CALL_DOCUMENTATION in any utility config's additional_settings
                utility_configs = [
                    kiosk_config.pos_terminal_config,
                    kiosk_config.fiscal_device_config,
                    kiosk_config.printer_device_config,
                    kiosk_config.kds_config
                ]
                
                for utility_config in utility_configs:
                    if utility_config and utility_config.additional_settings:
                        if utility_config.additional_settings.get('EXTERNAL_CALL_DOCUMENTATION', False):
                            logger.info(f"External call documentation enabled for kiosk {kiosk_username}")
                            return True
            
            logger.info(f"External call documentation disabled for kiosk {kiosk_username}")
            return False
            
        except Exception as e:
            logger.warning(f"Failed to check documentation setting for kiosk {kiosk_username}: {e}")
            return False
    
    def document_external_call(
        self,
        kiosk_username: str,
        service_type: str,
        operation_name: str,
        url: str,
        method: str = "POST",
        headers: Optional[Dict[str, str]] = None,
        request_body: Optional[Dict[str, Any]] = None,
        response_status: Optional[int] = None,
        response_body: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        duration_seconds: Optional[float] = None
    ) -> Optional[str]:
        """
        Document an external API call with full details.
        
        Args:
            kiosk_username: The kiosk making the call
            service_type: Type of service (payment, fiscal, kds, printer)
            operation_name: Name of the operation (e.g., process_payment, fiscalization)
            url: The full URL being called
            method: HTTP method (GET, POST, etc.)
            headers: Request headers
            request_body: Request payload
            response_status: HTTP response status code
            response_body: Response payload
            error_message: Error message if call failed
            duration_seconds: Call duration in seconds
            
        Returns:
            Path to the generated documentation file, or None if documentation disabled
        """
        if not self.should_document_calls(kiosk_username):
            return None
        
        try:
            # Resolve base directory from kiosk YAML (single source of truth)
            base_dir_str = _get_kiosk_additional_setting(kiosk_username, EXTERNAL_LOG_BASE_KEY)
            if not base_dir_str:
                logger.warning(f"External call docs: base path not set for kiosk {kiosk_username}; skipping")
                return None

            base_dir = Path(base_dir_str)

            # Validate that base exists and is writable; do not create base
            try:
                if not base_dir.exists() or not base_dir.is_dir():
                    logger.warning(f"External call docs: base does not exist for kiosk {kiosk_username}: {base_dir}; skipping")
                    return None
                if not os.access(str(base_dir), os.W_OK):
                    logger.warning(f"External call docs: base not writable for kiosk {kiosk_username}: {base_dir}; skipping")
                    return None
            except Exception as _e:
                logger.warning(f"External call docs: failed to validate base for kiosk {kiosk_username}: {base_dir}; skipping")
                return None

            # Build documentation directory under existing base:
            # base/DEBUG_ExternalCallDocumented/kiosk_{username}/{service}_calls/
            doc_root = base_dir / "DEBUG_ExternalCallDocumented"
            kiosk_dir = doc_root / kiosk_username
            service_dir = kiosk_dir / f"{service_type}_calls"

            # Create only subfolders under existing base
            service_dir.mkdir(parents=True, exist_ok=True)

            # Generate filename with timestamp
            timestamp = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"{timestamp}_{operation_name}.md"
            file_path = service_dir / filename
            
            # Generate documentation content
            content = self.generate_call_documentation(
                kiosk_username=kiosk_username,
                service_type=service_type,
                operation_name=operation_name,
                url=url,
                method=method,
                headers=headers or {},
                request_body=request_body,
                response_status=response_status,
                response_body=response_body,
                error_message=error_message,
                duration_seconds=duration_seconds
            )
            
            # Write documentation file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"External call documented: {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Failed to document external call for {kiosk_username}: {e}")
            return None
    
    def generate_call_documentation(
        self,
        kiosk_username: str,
        service_type: str,
        operation_name: str,
        url: str,
        method: str,
        headers: Dict[str, str],
        request_body: Optional[Dict[str, Any]],
        response_status: Optional[int],
        response_body: Optional[Dict[str, Any]],
        error_message: Optional[str],
        duration_seconds: Optional[float]
    ) -> str:
        """Generate markdown documentation for an external call"""
        
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        
        # Generate curl command
        curl_command = self.generate_curl_command(url, method, headers, request_body)
        
        # Build documentation content
        content = f"""# {service_type.title()} Call - {operation_name}

**Timestamp:** {timestamp}  
**Kiosk:** {kiosk_username}  
**Service:** {service_type.title()}  
**Operation:** {operation_name}  
"""
        
        if duration_seconds is not None:
            content += f"**Duration:** {duration_seconds:.3f}s  \n"
        
        content += f"""
## Request Details
**URL:** `{url}`  
**Method:** `{method}`  

### Headers
```json
{json.dumps(headers, indent=2)}
```

## Curl Command
```bash
{curl_command}
```
"""
        
        if request_body:
            content += f"""
## Request Body
```json
{json.dumps(request_body, indent=2)}
```
"""
        
        # Response section
        if response_status is not None:
            status_emoji = "✅" if 200 <= response_status < 300 else "❌"
            content += f"""
## Response
**Status:** {response_status} {status_emoji}  
"""
            
            if response_body:
                content += f"""
**Body:**
```json
{json.dumps(response_body, indent=2)}
```
"""
        
        # Error section
        if error_message:
            content += f"""
## Error
```
{error_message}
```
"""
        
        # Add footer
        content += f"""
---
*Generated by ExternalCallDocumenter*  
*File: {operation_name} - {timestamp}*
"""
        
        return content
    
    def generate_curl_command(
        self,
        url: str,
        method: str,
        headers: Dict[str, str],
        request_body: Optional[Dict[str, Any]]
    ) -> str:
        """Generate a curl command equivalent to the API call"""
        
        curl_parts = [f'curl -X {method.upper()} "{url}"']
        
        # Add headers
        for key, value in headers.items():
            curl_parts.append(f'  -H "{key}: {value}"')
        
        # Add request body if present
        if request_body:
            json_body = json.dumps(request_body, separators=(',', ':'))
            # Escape quotes for shell
            escaped_body = json_body.replace('"', '\\"')
            curl_parts.append(f'  -d "{escaped_body}"')
        
        return ' \\\n'.join(curl_parts)
    
    def get_kiosk_call_summary(self, kiosk_username: str) -> Dict[str, Any]:
        """Get summary of documented calls for a kiosk"""
        try:
            kiosk_dir = self.base_path / kiosk_username
            if not kiosk_dir.exists():
                return {"total_calls": 0, "services": {}}
            
            summary = {"total_calls": 0, "services": {}}
            
            for service_dir in kiosk_dir.iterdir():
                if service_dir.is_dir() and service_dir.name.endswith('_calls'):
                    service_name = service_dir.name.replace('_calls', '')
                    call_files = list(service_dir.glob('*.md'))
                    summary["services"][service_name] = len(call_files)
                    summary["total_calls"] += len(call_files)
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get call summary for {kiosk_username}: {e}")
            return {"total_calls": 0, "services": {}, "error": str(e)}
    
    def cleanup_old_documentation(self, days_to_keep: int = 7):
        """Clean up documentation files older than specified days"""
        try:
            cutoff_time = datetime.utcnow().timestamp() - (days_to_keep * 24 * 3600)
            deleted_count = 0
            
            for kiosk_dir in self.base_path.iterdir():
                if not kiosk_dir.is_dir():
                    continue
                    
                for service_dir in kiosk_dir.iterdir():
                    if not service_dir.is_dir():
                        continue
                        
                    for doc_file in service_dir.glob('*.md'):
                        if doc_file.stat().st_mtime < cutoff_time:
                            doc_file.unlink()
                            deleted_count += 1
            
            logger.info(f"Cleaned up {deleted_count} old documentation files")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old documentation: {e}")
            return 0


# Global documenter instance
_documenter: Optional[ExternalCallDocumenter] = None


def get_external_call_documenter() -> ExternalCallDocumenter:
    """Get or create global external call documenter instance"""
    global _documenter
    if _documenter is None:
        _documenter = ExternalCallDocumenter()
    return _documenter


def document_external_call(
    kiosk_username: str,
    service_type: str,
    operation_name: str,
    url: str,
    method: str = "POST",
    headers: Optional[Dict[str, str]] = None,
    request_body: Optional[Dict[str, Any]] = None,
    response_status: Optional[int] = None,
    response_body: Optional[Dict[str, Any]] = None,
    error_message: Optional[str] = None,
    duration_seconds: Optional[float] = None
) -> Optional[str]:
    """
    Convenience function to document an external API call.
    Returns path to documentation file if created, None if documentation disabled.
    """
    documenter = get_external_call_documenter()
    return documenter.document_external_call(
        kiosk_username=kiosk_username,
        service_type=service_type,
        operation_name=operation_name,
        url=url,
        method=method,
        headers=headers,
        request_body=request_body,
        response_status=response_status,
        response_body=response_body,
        error_message=error_message,
        duration_seconds=duration_seconds
    )