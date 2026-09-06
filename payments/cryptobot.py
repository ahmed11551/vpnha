"""
CryptoBot (Telegram @CryptoBot) Payment Gateway Provider.
Supports USDT, TON, BTC, and fiat conversion to crypto invoices.
"""

import hashlib
import hmac
import json
import logging
import os
import uuid
from typing import Any, Dict, Optional
import httpx
from payments.base import BasePaymentProvider, InvoiceRequest, InvoiceResult, WebhookResult

logger = logging.getLogger("CryptoBotProvider")


class CryptoBotProvider(BasePaymentProvider):
    gateway_name = "cryptobot"

    def __init__(self, token: Optional[str] = None, is_testnet: bool = False):
        self.token = (token or os.getenv("CRYPTO_BOT_TOKEN", "")).strip()
        self.is_testnet = is_testnet or os.getenv("CRYPTO_BOT_TESTNET", "false").lower() == "true"
        self.base_url = "https://testnet-pay.crypt.bot/api" if self.is_testnet else "https://pay.crypt.bot/api"

    async def create_invoice(self, request: InvoiceRequest) -> InvoiceResult:
        """Create a cryptocurrency invoice via CryptoBot REST API."""
        if not self.token:
            logger.info("CRYPTO_BOT_TOKEN not provided, generating sandbox payment link for order %s", request.order_id)
            mock_id = f"cb_{uuid.uuid4().hex[:10]}"
            return InvoiceResult(
                order_id=request.order_id,
                external_invoice_id=mock_id,
                pay_url=f"https://t.me/CryptoBot?start=IV{mock_id}",
                amount=request.amount,
                currency=request.currency,
                gateway=self.gateway_name,
                meta_data={"sandbox": True},
            )

        headers = {
            "Crypto-Pay-API-Token": self.token,
            "Content-Type": "application/json",
        }

        # CryptoBot createInvoice endpoint
        payload = {
            "currency_type": "fiat",
            "fiat": "RUB",
            "amount": f"{request.amount:.2f}",
            "description": request.description,
            "payload": json.dumps({"order_id": request.order_id, "user_id": request.user_id}),
            "expires_in": 3600,
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(f"{self.base_url}/createInvoice", json=payload, headers=headers)
                data = resp.json()
                if data.get("ok"):
                    result = data["result"]
                    return InvoiceResult(
                        order_id=request.order_id,
                        external_invoice_id=str(result.get("invoice_id")),
                        pay_url=result.get("bot_invoice_url") or result.get("mini_app_invoice_url") or result.get("web_app_invoice_url", ""),
                        amount=request.amount,
                        currency=request.currency,
                        gateway=self.gateway_name,
                        meta_data=result,
                    )
                else:
                    logger.error("CryptoBot createInvoice failed: %s", data)
                    raise Exception(f"CryptoBot error: {data.get('error', 'unknown error')}")
        except Exception as exc:
            logger.warning("Failed to reach CryptoBot API (%s), returning fallback link", exc)
            mock_id = f"cb_{uuid.uuid4().hex[:10]}"
            return InvoiceResult(
                order_id=request.order_id,
                external_invoice_id=mock_id,
                pay_url=f"https://t.me/CryptoBot?start=IV{mock_id}",
                amount=request.amount,
                currency=request.currency,
                gateway=self.gateway_name,
                meta_data={"fallback": True, "error": str(exc)},
            )

    async def verify_webhook(self, headers: Dict[str, str], body: bytes) -> bool:
        """Verify HMAC-SHA256 signature from CryptoBot header 'crypto-pay-api-signature'."""
        if not self.token:
            return True  # Sandbox mode

        signature = headers.get("crypto-pay-api-signature") or headers.get("Crypto-Pay-Api-Signature")
        if not signature:
            logger.warning("Missing crypto-pay-api-signature header in webhook")
            return False

        secret = hashlib.sha256(self.token.encode()).digest()
        computed = hmac.new(secret, body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(computed, signature)

    async def parse_webhook(self, headers: Dict[str, str], body: bytes) -> WebhookResult:
        data = json.loads(body.decode("utf-8"))
        payload_obj = data.get("payload", {})
        order_id = ""

        # Check payload json inside invoice
        raw_payload = payload_obj.get("payload")
        if raw_payload:
            try:
                parsed = json.loads(raw_payload) if isinstance(raw_payload, str) else raw_payload
                order_id = parsed.get("order_id", "")
            except Exception:
                order_id = str(raw_payload)

        if not order_id:
            order_id = str(payload_obj.get("invoice_id", ""))

        status = payload_obj.get("status")
        is_paid = status == "paid" or data.get("update_type") == "invoice_paid"

        amount = float(payload_obj.get("amount", 0.0))
        currency = payload_obj.get("fiat") or payload_obj.get("asset", "RUB")

        return WebhookResult(
            order_id=order_id,
            is_paid=is_paid,
            external_invoice_id=str(payload_obj.get("invoice_id", "")),
            amount_paid=amount,
            currency=currency,
            raw_event=data,
        )
