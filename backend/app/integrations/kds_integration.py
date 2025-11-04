# kds_integration.py
# Kitchen Display System integration with mockup functionality for testing

import asyncio
import uuid
import aiohttp
from typing import Dict, Any, Optional, List
from decimal import Decimal
from datetime import datetime
from dataclasses import dataclass
from enum import Enum


class KDSResult(str, Enum):
    """KDS processing results"""
    CONFIRMED = "CONFIRMED"
    ERROR = "ERROR"
    NO_RESPONSE = "NO_RESPONSE"
    TIMEOUT = "TIMEOUT"


class OrderPriority(str, Enum):
    """Order priority levels for kitchen"""
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    URGENT = "URGENT"


@dataclass
class KDSOrderItem:
    """Order item structure for KDS matching web emulator API"""
    item_id: int
    description: str
    quantity: int


@dataclass
class KDSRequest:
    """KDS request structure matching web emulator API"""
    order_id: int
    kiosk_id: str
    items: List[KDSOrderItem]


@dataclass
class KDSResponse:
    """KDS response structure matching web emulator API"""
    status: str  # OK|NOT_OK
    kds_ticket_id: Optional[str] = None
    received_at: Optional[str] = None  # ISO datetime string
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    processed_at: datetime = None
    
    def __post_init__(self):
        if self.processed_at is None:
            self.processed_at = datetime.utcnow()


class KDSGatewayConfig:
    """Configuration for KDS integration"""

    def __init__(self, kiosk_username: Optional[str] = None):
        # Load from centralized config with kiosk-specific overrides
        from .integrations_config import get_integrations_config
        config = get_integrations_config(kiosk_username).kds

        # Copy settings from centralized config (now kiosk-specific)
        self.mockup_mode = config.mockup_mode
        self.kds_api_url = config.kds_api_url
        self.kds_endpoint = config.kds_endpoint
        self.kds_api_key = config.kds_api_key
        self.kds_timeout = config.timeout_seconds
        self.kitchen_station_id = config.kitchen_station_id
        self.auto_confirm_orders = config.auto_confirm_orders
        self.use_ssl = config.use_ssl
        self.max_retries = config.max_retries
        self.timeout_seconds = config.timeout_seconds

        # Mockup-specific settings (keep for backward compatibility)
        self.mockup_success_rate = 0.95  # 95% success rate for KDS
        self.mockup_processing_delay = 0.5  # seconds
        self.mockup_prep_time_minutes = 15  # Default preparation time
        self.default_prep_time = 15  # minutes
        self.priority_prep_time_multiplier = 0.8  # High priority orders get 20% less time


class KDSGateway:
    """
    Kitchen Display System integration service.
    Currently implements mockup functionality for testing.
    """
    
    def __init__(self, config: KDSGatewayConfig):
        self.config = config
        self._order_counter = 1
    
    def _get_kiosk_specific_config(self, kiosk_username: str):
        """Get kiosk-specific KDS configuration"""
        from .integrations_config import get_integrations_config
        return get_integrations_config(kiosk_username).kds
    
    async def send_order_to_kitchen(self, request: KDSRequest, kiosk_username: str) -> KDSResponse:
        """
        Send order to kitchen display system with kiosk-specific configuration.
        Resolves kiosk-specific settings internally for address, timeout, and retry parameters.
        """
        # Get kiosk-specific configuration
        kiosk_config = self._get_kiosk_specific_config(kiosk_username)
        
        if kiosk_config.mockup_mode:
            return await self._mockup_kds_processing(request, kiosk_config)
        else:
            return await self._real_kds_processing(request, kiosk_config)
    
    async def _mockup_kds_processing(self, request: KDSRequest, kiosk_config) -> KDSResponse:
        """Mockup KDS processing for testing with kiosk-specific configuration."""
        import time
        from ..integrations.external_call_documenter import document_external_call
        
        # Track operation for documentation
        start_time = time.time()
        
        # Simulate processing delay
        await asyncio.sleep(self.config.mockup_processing_delay)
        
        self._order_counter += 1
        
        # Simulate success/failure based on configured rate
        import random
        is_success = random.random() < self.config.mockup_success_rate
        
        if is_success:
            kds_ticket_id = f"KDS{self._order_counter:04d}"
            
            kds_response = KDSResponse(
                status="OK",
                kds_ticket_id=kds_ticket_id,
                received_at=datetime.utcnow().isoformat()
            )
            
            # Document mockup operation
            duration = time.time() - start_time
            document_external_call(
                kiosk_username=request.kiosk_id,
                service_type="kds",
                operation_name="send_order_to_kitchen_mockup",
                url="mockup_mode",
                method="LOCAL",
                headers={},
                request_body={
                    "order_id": request.order_id,
                    "kiosk_id": request.kiosk_id,
                    "items": [
                        {
                            "item_id": item.item_id,
                            "description": item.description,
                            "quantity": item.quantity
                        }
                        for item in request.items
                    ]
                },
                response_status=200,
                response_body={
                    "status": "OK",
                    "kds_ticket_id": kds_ticket_id,
                    "received_at": datetime.utcnow().isoformat()
                },
                duration_seconds=duration
            )
            
            return kds_response
        else:
            # Simulate different failure types
            failure_types = [
                ("01", "Kitchen system offline", KDSResult.ERROR),
                ("02", "Invalid order data", KDSResult.ERROR),
                ("TIMEOUT", "Kitchen system timeout", KDSResult.TIMEOUT),
                ("NO_RESP", "No response from kitchen", KDSResult.NO_RESPONSE)
            ]
            
            code, message, result = random.choice(failure_types)
            
            kds_response = KDSResponse(
                status="NOT_OK",
                error_code=code,
                error_message=message
            )
            
            # Document mockup failure
            duration = time.time() - start_time
            document_external_call(
                kiosk_username=request.kiosk_id,
                service_type="kds",
                operation_name="send_order_to_kitchen_mockup",
                url="mockup_mode",
                method="LOCAL",
                headers={},
                request_body={
                    "order_id": request.order_id,
                    "kiosk_id": request.kiosk_id,
                    "items": [
                        {
                            "item_id": item.item_id,
                            "description": item.description,
                            "quantity": item.quantity
                        }
                        for item in request.items
                    ]
                },
                response_status=500,
                response_body={
                    "status": "NOT_OK",
                    "error_code": code,
                    "error_message": message
                },
                error_message=message,
                duration_seconds=duration
            )
            
            return kds_response
    
    async def _real_kds_processing(self, request: KDSRequest, kiosk_config) -> KDSResponse:
        """
        Real KDS processing integration with web emulator.
        Calls the actual kitchen system/emulator via HTTP using kiosk-specific configuration.
        """
        import json
        import time
        from ..integrations.external_call_documenter import document_external_call
        
        if not kiosk_config.kds_api_url:
            raise Exception(f"KDS API URL not configured for kiosk {request.kiosk_id}")
        
        # Prepare request payload matching web emulator format
        payload = {
            "order_id": request.order_id,
            "kiosk_id": request.kiosk_id,
            "items": [
                {
                    "item_id": item.item_id,
                    "description": item.description,
                    "quantity": item.quantity
                }
                for item in request.items
            ]
        }
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Header-Kiosk-Id": request.kiosk_id,
            "Header-Operation-Type": "kds",
            "Header-Method": "POST"
        }
        
        if kiosk_config.kds_api_key:
            headers["Authorization"] = f"Bearer {kiosk_config.kds_api_key}"
        
        # Track call duration for documentation
        start_time = time.time()
        response_status = None
        response_data = None
        error_message = None
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=kiosk_config.timeout_seconds)) as session:
                # Use kds_api_url with configurable endpoint path
                full_url = f"{kiosk_config.kds_api_url}{kiosk_config.kds_endpoint}"
                async with session.post(
                    full_url,
                    json=payload,
                    headers=headers,
                    ssl=kiosk_config.use_ssl
                ) as response:
                    response_status = response.status
                    
                    if response.status == 200:
                        # Parse response
                        response_data = await response.json()
                        
                        # Document the call
                        duration = time.time() - start_time
                        document_external_call(
                            kiosk_username=request.kiosk_id,
                            service_type="kds",
                            operation_name="send_order_to_kitchen",
                            url=full_url,
                            method="POST",
                            headers=headers,
                            request_body=payload,
                            response_status=response_status,
                            response_body=response_data,
                            duration_seconds=duration
                        )
                        
                        if response_data.get("status") == "OK":
                            # Success response
                            return KDSResponse(
                                status="OK",
                                kds_ticket_id=response_data.get("kds_ticket_id"),
                                received_at=response_data.get("received_at")
                            )
                        else:
                            # Failure response
                            return KDSResponse(
                                status="NOT_OK",
                                error_code=response_data.get("error_code", "UNKNOWN"),
                                error_message=response_data.get("error_message", "KDS processing failed")
                            )
                    
                    else:
                        # Handle error responses
                        if response.status == 503:
                            error_message = "KDS service unavailable"
                            response_data = {"error": error_message}
                            kds_response = KDSResponse(
                                status="NOT_OK",
                                error_code="SERVICE_UNAVAILABLE",
                                error_message=error_message
                            )
                        elif response.status == 500:
                            error_message = "KDS service internal error"
                            response_data = {"error": error_message}
                            kds_response = KDSResponse(
                                status="NOT_OK",
                                error_code="INTERNAL_ERROR",
                                error_message=error_message
                            )
                        else:
                            error_detail = await response.text()
                            error_message = f"HTTP {response.status}: {error_detail}"
                            response_data = {"error": error_message}
                            kds_response = KDSResponse(
                                status="NOT_OK",
                                error_code=f"HTTP_{response.status}",
                                error_message=error_message
                            )
                        
                        # Document error responses
                        duration = time.time() - start_time
                        document_external_call(
                            kiosk_username=request.kiosk_id,
                            service_type="kds",
                            operation_name="send_order_to_kitchen",
                            url=full_url,
                            method="POST",
                            headers=headers,
                            request_body=payload,
                            response_status=response_status,
                            response_body=response_data,
                            error_message=error_message,
                            duration_seconds=duration
                        )
                        return kds_response
        
        except aiohttp.ClientTimeout:
            error_message = "KDS gateway timeout"
            duration = time.time() - start_time
            
            # Document timeout
            document_external_call(
                kiosk_username=request.kiosk_id,
                service_type="kds",
                operation_name="send_order_to_kitchen",
                url=full_url,
                method="POST",
                headers=headers,
                request_body=payload,
                error_message=error_message,
                duration_seconds=duration
            )
            
            return KDSResponse(
                status="NOT_OK",
                error_code="TIMEOUT",
                error_message=error_message
            )
        
        except Exception as e:
            error_message = f"KDS processing error: {str(e)}"
            duration = time.time() - start_time
            
            # Document exception
            document_external_call(
                kiosk_username=request.kiosk_id,
                service_type="kds",
                operation_name="send_order_to_kitchen",
                url=full_url,
                method="POST",
                headers=headers,
                request_body=payload,
                error_message=error_message,
                duration_seconds=duration
            )
            
            return KDSResponse(
                status="NOT_OK",
                error_code="ERROR",
                error_message=error_message
            )
    
    async def check_order_status(self, kds_order_id: str) -> Optional[Dict[str, Any]]:
        """
        Check order status in kitchen system.
        Used for polling order completion status.
        """
        if self.config.mockup_mode:
            # In mockup mode, simulate random completion
            import random
            if random.random() < 0.1:  # 10% chance order is ready
                return {
                    "kds_order_id": kds_order_id,
                    "status": "READY",
                    "completed_at": datetime.utcnow().isoformat(),
                    "notes": "Order ready for pickup"
                }
            return None
        else:
            # TODO: Implement real status checking
            raise NotImplementedError("Real KDS status checking not implemented yet")


# Global KDS gateway instance
_kds_gateway: Optional[KDSGateway] = None


def get_kds_gateway() -> KDSGateway:
    """Get or create KDS gateway instance."""
    global _kds_gateway
    if _kds_gateway is None:
        config = KDSGatewayConfig()
        _kds_gateway = KDSGateway(config)
    return _kds_gateway


def configure_kds_gateway(config: KDSGatewayConfig) -> None:
    """Configure KDS gateway with custom settings."""
    global _kds_gateway
    _kds_gateway = KDSGateway(config)