"""
Base abstract payment provider interface for NexusVPN Commercial Platform.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class InvoiceRequest(BaseModel):
    order_id: str
    user_id: int
    telegram_id: int
    amount: float = Field(..., gt=0)
    currency: str = "RUB"
    description: str = "NexusVPN Subscription"
    plan_id: Optional[str] = None
    promo_code: Optional[str] = None
    return_url: Optional[str] = None


class InvoiceResult(BaseModel):
    order_id: str
    external_invoice_id: str
    pay_url: str
    amount: float
    currency: str
    gateway: str
    meta_data: Optional[Dict[str, Any]] = None


class WebhookResult(BaseModel):
    order_id: str
    is_paid: bool
    external_invoice_id: Optional[str] = None
    amount_paid: Optional[float] = None
    currency: Optional[str] = None
    raw_event: Optional[Dict[str, Any]] = None


class BasePaymentProvider(ABC):
    """Abstract interface for commercial payment gateways."""

    gateway_name: str = "base"

    @abstractmethod
    async def create_invoice(self, request: InvoiceRequest) -> InvoiceResult:
        """Create a payment invoice with the provider and return payment URL."""
        pass

    @abstractmethod
    async def verify_webhook(self, headers: Dict[str, str], body: bytes) -> bool:
        """Verify the cryptographic signature of the webhook."""
        pass

    @abstractmethod
    async def parse_webhook(self, headers: Dict[str, str], body: bytes) -> WebhookResult:
        """Parse the webhook payload into normalized WebhookResult."""
        pass
