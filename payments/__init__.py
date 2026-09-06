"""
Payment provider registry and factory.
"""

from typing import Dict
from payments.base import BasePaymentProvider, InvoiceRequest, InvoiceResult, WebhookResult
from payments.cryptobot import CryptoBotProvider
from payments.stars import TelegramStarsProvider
from payments.yookassa import YooKassaProvider

_providers: Dict[str, BasePaymentProvider] = {
    "cryptobot": CryptoBotProvider(),
    "stars": TelegramStarsProvider(),
    "yookassa": YooKassaProvider(),
    "card": YooKassaProvider(),  # Alias for credit card / SBP
    "sbp": YooKassaProvider(),
}


def get_payment_provider(gateway_name: str) -> BasePaymentProvider:
    """Retrieve payment provider by gateway name."""
    clean_name = gateway_name.lower().strip()
    provider = _providers.get(clean_name)
    if not provider:
        # Default to CryptoBot if unrecognized
        return _providers["cryptobot"]
    return provider


__all__ = [
    "BasePaymentProvider",
    "InvoiceRequest",
    "InvoiceResult",
    "WebhookResult",
    "CryptoBotProvider",
    "TelegramStarsProvider",
    "YooKassaProvider",
    "get_payment_provider",
]
