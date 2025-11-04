# printer_gateway.py
# Printer gateway integration with file-based printing for testing
# Prints realistic POS terminal receipts to /receipts folder
# Single-path policy integration notes:
# - Receipts folder is resolved from kiosk YAML INTEGRATIONS_LOG_BASE_PATH as: base/DEBUG_receipts
# - If base path is missing/invalid/not writable: skip receipt file writing with a short log
# - Do NOT create base directory; only create receipts subfolder under existing base if allowed

import asyncio
import os
from typing import Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import logging


logger = logging.getLogger(__name__)


class PrinterResult(str, Enum):
    """Printer processing results"""
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    ERROR = "ERROR"
    TIMEOUT = "TIMEOUT"


@dataclass
class PrinterRequest:
    """Printer request structure for receipt printing"""
    order_id: int
    kiosk_id: str
    payment_data: Dict[str, Any]  # Payment response data for receipt
    receipt_type: str = "CUSTOMER"  # CUSTOMER or MERCHANT


@dataclass
class PrinterResponse:
    """Printer response structure"""
    status: str  # SUCCESS|FAILED|ERROR
    receipt_file_path: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    printed_at: datetime = None
    
    def __post_init__(self):
        if self.printed_at is None:
            self.printed_at = datetime.utcnow()


class PrinterGatewayConfig:
    """Configuration for printer gateway integration"""
    
    def __init__(self, kiosk_username: Optional[str] = None):
        # Load from centralized config with kiosk-specific overrides
        from .integrations_config import get_integrations_config
        config = get_integrations_config(kiosk_username).printer
        
        # Copy settings from centralized config (now kiosk-specific)
        self.mockup_mode = config.mockup_mode
        self.receipts_folder = config.receipts_folder
        self.printer_host = config.printer_host
        self.printer_endpoint = config.printer_endpoint
        self.printer_port = config.printer_port
        self.printer_model = config.printer_model
        self.timeout_seconds = config.timeout_seconds
        self.max_retries = config.max_retries
        
        # Mockup-specific settings (keep for backward compatibility)
        self.mockup_success_rate = 0.95  # 95% success rate for printing
        self.mockup_processing_delay = 0.5  # seconds


class PrinterGateway:
    """
    Printer gateway integration service.
    Currently implements file-based printing for testing.
    """
    
    def __init__(self, config: PrinterGatewayConfig):
        self.config = config
        self._receipt_counter = 1

        # Defer receipts subfolder creation to print time with kiosk-specific base path
        try:
            if self.config.receipts_folder:
                logger.info("Printer receipts: global receipts_folder present; creation deferred to print time")
            else:
                logger.info("Printer receipts: no global receipts_folder; will resolve per kiosk at print time")
        except Exception:
            logger.warning("Printer receipts: init check failed; will resolve per kiosk at print time")

    def _resolve_kiosk_receipts_folder(self, kiosk_username: str) -> str:
        """
        Resolve receipts folder from kiosk YAML INTEGRATIONS_LOG_BASE_PATH.
        Returns empty string if base missing/invalid/not writable.
        """
        try:
            from ..kiosk_configuration_service import get_kiosk_configuration_service
            kiosk_service = get_kiosk_configuration_service()
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
            if not log_base:
                logger.warning(f"Printer receipts: INTEGRATIONS_LOG_BASE_PATH not set for kiosk {kiosk_username}")
                return ""
            base_dir = Path(log_base)
            if base_dir.exists() and base_dir.is_dir() and os.access(str(base_dir), os.W_OK):
                return str(base_dir / "DEBUG_receipts")
            logger.warning(f"Printer receipts: base invalid or not writable for kiosk {kiosk_username}: {base_dir}")
            return ""
        except Exception as _e:
            logger.warning(f"Printer receipts: failed to resolve base path for kiosk {kiosk_username}")
            return ""
    
    def _get_kiosk_specific_config(self, kiosk_username: str):
        """Get kiosk-specific printer configuration"""
        from .integrations_config import get_integrations_config
        return get_integrations_config(kiosk_username).printer
    
    async def print_receipt(self, request: PrinterRequest, kiosk_username: str) -> PrinterResponse:
        """
        Print receipt to file with kiosk-specific configuration.
        Resolves kiosk-specific settings internally for address, timeout, and retry parameters.
        """
        import time
        from ..integrations.external_call_documenter import document_external_call
        
        # Get kiosk-specific configuration
        kiosk_config = self._get_kiosk_specific_config(kiosk_username)

        # Resolve receipts folder per kiosk based on INTEGRATIONS_LOG_BASE_PATH (single-path policy)
        receipts_dir_override = self._resolve_kiosk_receipts_folder(kiosk_username)
        if not receipts_dir_override:
            logger.warning(f"Printer receipts: no kiosk override resolved for {kiosk_username}; global={self.config.receipts_folder}")
        
        # Track operation for documentation
        start_time = time.time()
        
        if kiosk_config.mockup_mode:
            result = await self._mockup_receipt_printing(request, kiosk_config, receipts_dir_override)
            
            # Document mockup operation
            duration = time.time() - start_time
            document_external_call(
                kiosk_username=kiosk_username,
                service_type="printer",
                operation_name="print_receipt_mockup",
                url="mockup_mode",
                method="LOCAL",
                headers={},
                request_body={
                    "order_id": request.order_id,
                    "kiosk_id": request.kiosk_id,
                    "receipt_type": request.receipt_type
                },
                response_status=200 if result.status == "SUCCESS" else 500,
                response_body={
                    "status": result.status,
                    "receipt_file_path": result.receipt_file_path,
                    "error_message": result.error_message
                },
                duration_seconds=duration
            )
            
            return result
        else:
            return await self._real_receipt_printing(request, kiosk_config)
    
    async def _mockup_receipt_printing(self, request: PrinterRequest, kiosk_config, receipts_dir_override: Optional[str] = None) -> PrinterResponse:
        """Mockup receipt printing for testing with kiosk-specific configuration."""
        # Simulate processing delay
        await asyncio.sleep(self.config.mockup_processing_delay)
        
        self._receipt_counter += 1
        
        # Simulate success/failure based on configured rate
        import random
        is_success = random.random() < self.config.mockup_success_rate
        
        if is_success:
            # Determine target receipts folder: use ONLY per-kiosk override (single-path policy, no fallback)
            receipts_dir = receipts_dir_override or ""
            if not receipts_dir:
                logger.warning(f"Printer receipts: folder not configured for kiosk {request.kiosk_id}; skipping file write")
                return PrinterResponse(
                    status="SUCCESS",
                    receipt_file_path=None
                )

            # Attempt to ensure receipts subfolder exists if base allows it
            try:
                receipts_path = Path(receipts_dir)
                base_parent = receipts_path.parent
                if not receipts_path.exists():
                    if base_parent.exists() and base_parent.is_dir() and os.access(str(base_parent), os.W_OK):
                        receipts_path.mkdir(parents=True, exist_ok=True)
                    else:
                        logger.warning(f"Printer receipts: base invalid for kiosk {request.kiosk_id}; skipping file write")
                        return PrinterResponse(
                            status="SUCCESS",
                            receipt_file_path=None
                        )

                if not os.access(str(receipts_path), os.W_OK):
                    logger.warning(f"Printer receipts: folder not writable for kiosk {request.kiosk_id}: {receipts_path}; skipping file write")
                    return PrinterResponse(
                        status="SUCCESS",
                        receipt_file_path=None
                    )
            except Exception as _e:
                logger.warning(f"Printer receipts: failed to prepare folder for kiosk {request.kiosk_id}; skipping file write")
                return PrinterResponse(
                    status="SUCCESS",
                    receipt_file_path=None
                )

            # Generate receipt content
            receipt_content = self._generate_pos_terminal_receipt(request)

            # Create filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"receipt_order_{request.order_id}_{timestamp}.txt"
            file_path = os.path.join(receipts_dir, filename)

            # Write receipt to file
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(receipt_content)

                return PrinterResponse(
                    status="SUCCESS",
                    receipt_file_path=file_path
                )
            except Exception as e:
                logger.warning(f"Printer receipts: file write error for kiosk {request.kiosk_id}: {e}; skipping")
                return PrinterResponse(
                    status="SUCCESS",
                    receipt_file_path=None
                )
        else:
            # Simulate different failure types
            failure_types = [
                ("PAPER_JAM", "Printer paper jam", PrinterResult.FAILED),
                ("OUT_OF_PAPER", "Printer out of paper", PrinterResult.FAILED),
                ("PRINTER_OFFLINE", "Printer offline", PrinterResult.ERROR),
                ("TIMEOUT", "Printer timeout", PrinterResult.TIMEOUT)
            ]
            
            code, message, result = random.choice(failure_types)
            
            return PrinterResponse(
                status=result.value,
                error_code=code,
                error_message=message
            )
    
    async def _real_receipt_printing(self, request: PrinterRequest, kiosk_config) -> PrinterResponse:
        """
        Real printer integration with external printer service via HTTP.
        Calls the actual printer service/emulator via HTTP using kiosk-specific configuration.
        """
        import json
        import time
        import aiohttp
        from ..integrations.external_call_documenter import document_external_call
        
        if not kiosk_config.printer_host:
            raise Exception(f"Printer service URL not configured for kiosk {request.kiosk_id}")
        
        # Prepare request payload for external printer service
        payload = {
            "order_id": request.order_id,
            "kiosk_id": request.kiosk_id,
            "receipt_type": request.receipt_type,
            "payment_data": request.payment_data
        }
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Header-Kiosk-Id": request.kiosk_id,
            "Header-Operation-Type": "print",
            "Header-Method": "POST"
        }
        
        # Track call duration for documentation
        start_time = time.time()
        response_status = None
        response_data = None
        error_message = None
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=kiosk_config.timeout_seconds)) as session:
                # Use printer_host with configurable endpoint path
                full_url = f"{kiosk_config.printer_host}{kiosk_config.printer_endpoint}"
                async with session.post(
                    full_url,
                    json=payload,
                    headers=headers
                ) as response:
                    response_status = response.status
                    
                    if response.status == 200:
                        # Parse successful response
                        response_data = await response.json()
                        
                        # Document the successful call
                        duration = time.time() - start_time
                        document_external_call(
                            kiosk_username=request.kiosk_id,
                            service_type="printer",
                            operation_name="print_receipt",
                            url=full_url,
                            method="POST",
                            headers=headers,
                            request_body=payload,
                            response_status=response_status,
                            response_body=response_data,
                            duration_seconds=duration
                        )
                        
                        # Map external printer response to our PrinterResponse format
                        return PrinterResponse(
                            status=response_data.get("status", "SUCCESS"),
                            receipt_file_path=response_data.get("receipt_file_path"),
                            error_code=response_data.get("error_code"),
                            error_message=response_data.get("error_message")
                        )
                    
                    else:
                        # Handle error responses
                        if response.status == 503:
                            error_message = "Printer service unavailable"
                            response_data = {"error": error_message}
                        elif response.status == 500:
                            error_message = "Printer service internal error"
                            response_data = {"error": error_message}
                        else:
                            error_detail = await response.text()
                            error_message = f"HTTP {response.status}: {error_detail}"
                            response_data = {"error": error_message}
                        
                        printer_response = PrinterResponse(
                            status="ERROR",
                            error_code=f"HTTP_{response.status}",
                            error_message=error_message
                        )
                        
                        # Document error responses
                        duration = time.time() - start_time
                        document_external_call(
                            kiosk_username=request.kiosk_id,
                            service_type="printer",
                            operation_name="print_receipt",
                            url=full_url,
                            method="POST",
                            headers=headers,
                            request_body=payload,
                            response_status=response_status,
                            response_body=response_data,
                            error_message=error_message,
                            duration_seconds=duration
                        )
                        return printer_response
        
        except aiohttp.ClientTimeout:
            error_message = "Printer service timeout"
            duration = time.time() - start_time
            
            # Document timeout
            document_external_call(
                kiosk_username=request.kiosk_id,
                service_type="printer",
                operation_name="print_receipt",
                url=full_url,
                method="POST",
                headers=headers,
                request_body=payload,
                error_message=error_message,
                duration_seconds=duration
            )
            
            return PrinterResponse(
                status="TIMEOUT",
                error_code="TIMEOUT",
                error_message=error_message
            )
        
        except Exception as e:
            error_message = f"Printer service error: {str(e)}"
            duration = time.time() - start_time
            
            # Document exception
            document_external_call(
                kiosk_username=request.kiosk_id,
                service_type="printer",
                operation_name="print_receipt",
                url=full_url,
                method="POST",
                headers=headers,
                request_body=payload,
                error_message=error_message,
                duration_seconds=duration
            )
            
            return PrinterResponse(
                status="ERROR",
                error_code="ERROR",
                error_message=error_message
            )
    
    def _generate_pos_terminal_receipt(self, request: PrinterRequest) -> str:
        """Generate realistic POS terminal receipt with ZERO CULTURE branding."""
        payment_data = request.payment_data
        now = datetime.now()
        
        # Extract payment details
        transaction_id = payment_data.get("transaction_id", "TXN_UNKNOWN")
        auth_code = payment_data.get("auth_code", "123456")
        rrn = payment_data.get("rrn", "000010000050")
        amount = payment_data.get("amount", 0)
        terminal_id = payment_data.get("terminal_id", "00092240")
        
        receipt_content = f"""================================
         ZERO CULTURE
================================
POS-Universal
           TEST TEST            
         VTID: XXXXXXX          
ТЕРМИНАЛ №:             {terminal_id}
ДАТА {now.strftime('%d/%m/%y')}     ВРЕМЯ {now.strftime('%H:%M:%S')}
ОПЛАТА ПОКУПКИ
MasterCard    НАЗНАЧЕНИЕ ПЛАТЕЖА
**** **** **** 4340
ПАКЕТ:0000            ЧЕК:{self._receipt_counter:04d}
ПЛАТЕЖНАЯ СИСТЕМА     MasterCard
ТИП КАРТЫ (APP)       Mastercard
             БЕСКОНТАКТНАЯ КАРТА
RRN:{rrn} КОД АВТ.:{auth_code}
AID: A0000000041010        
TVR:8000008001
ИТОГО                 {amount:.2f} RUB
КОД ОТВЕТА                    00
            ОДОБРЕНО            
ПОДПИСЬ КЛИЕНТА НЕ ТРЕБУЕТСЯ


================================
Thank you for your purchase!
================================

Order ID: {request.order_id}
Kiosk: {request.kiosk_id}
Transaction: {transaction_id}
Printed: {now.strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return receipt_content


# Global printer gateway instance
_printer_gateway: Optional[PrinterGateway] = None


def get_printer_gateway() -> PrinterGateway:
    """Get or create printer gateway instance."""
    global _printer_gateway
    if _printer_gateway is None:
        config = PrinterGatewayConfig()
        _printer_gateway = PrinterGateway(config)
    return _printer_gateway


def configure_printer_gateway(config: PrinterGatewayConfig) -> None:
    """Configure printer gateway with custom settings."""
    global _printer_gateway
    _printer_gateway = PrinterGateway(config)