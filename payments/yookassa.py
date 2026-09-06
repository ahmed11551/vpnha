"""
YooKassa (ЮKassa) Payment Gateway Provider for Russian Cards (МИР / Visa / MC) and СБП.
"""

import base64
import json
import logging
import os
import uuid
from typing import Any, Dict, Optional
import httpx
from payments.base import BasePaymentProvider, InvoiceRequest, InvoiceResult, WebhookResult

logger = logging.getLogger("YooKassaProvider")


class YooKassaProvider(BasePaymentProvider):
    gateway_name = "yookassa"

    def __init__(self, shop_id: Optional[str] = None, secret_key: Optional[str] = None):
        self.shop_id = (shop_id or os.getenv("YOOKASSA_SHOP_ID", "")).strip()
        self.secret_key = (secret_key or os.getenv("YOOKASSA_SECRET_KEY", "")).strip()
        self.base_url = "https://api.yookassa.ru/v3"

    async def create_invoice(self, request: InvoiceRequest) -> InvoiceResult:
        """Create a payment session via YooKassa API."""
        if not self.shop_id or not self.secret_key:
            logger.info("YooKassa credentials not set; generating sandbox payment session for order %s", request.order_id)
            mock_id = f"yk_{uuid.uuid4().hex[:12]}"
            return InvoiceResult(
                order_id=request.order_id,
                external_invoice_id=mock_id,
                pay_url=f"https://yookassa.ru/checkout?order={request.order_id}&mock=true",
                amount=request.amount,
                currency="RUB",
                gateway=self.gateway_name,
                meta_data={"sandbox": True},
            )

        auth_str = f"{self.shop_id}:{self.secret_key}"
        auth_bytes = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")

        headers = {
            "Authorization": f"Basic {auth_bytes}",
            "Idempotence-Key": request.order_id,
            "Content-Type": "application/json",
        }

        payload = {
            "amount": {
                "value": f"{request.amount:.2f}",
                "currency": "RUB",
            },
            "confirmation": {
                "type": "redirect",
                "return_url": request.return_url or "https://t.me/NexusVpnBot",
            },
            "capture": True,
            "description": f"{request.description} (Order {request.order_id})",
            "metadata": {
                "order_id": request.order_id,
                "user_id": str(request.user_id),
                "telegram_id": str(request.telegram_id),
            },
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(f"{self.base_url}/payments", json=payload, headers=headers)
                data = resp.json()
                if resp.status_code in (200, 201):
                    confirmation_url = data.get("confirmation", {}).get("confirmation_url", "")
                    return InvoiceResult(
                        order_id=request.order_id,
                        external_invoice_id=data.get("id"),
                        pay_url=confirmation_url,
                        amount=request.amount,
                        currency="RUB",
                        gateway=self.gateway_name,
                        meta_data=data,
                    )
                else:
                    logger.error("YooKassa payment creation error: %s", data)
                    raise Exception(f"YooKassa error: {data.get('description', 'unknown')}")
        except Exception as exc:
            logger.warning("YooKassa API communication failure (%s), returning fallback link", exc)
            mock_id = f"yk_{uuid.uuid4().hex[:12]}"
            return InvoiceResult(
                order_id=request.order_id,
                external_invoice_id=mock_id,
                pay_url=f"https://yookassa.ru/checkout?order={request.order_id}&mock=true",
                amount=request.amount,
                currency="RUB",
                gateway=self.gateway_name,
                meta_data={"fallback": True, "error": str(exc)},
            )

    async def verify_webhook(self, headers: Dict[str, str], body: bytes) -> bool:
        # YooKassa recommends checking source IP ranges or basic auth webhook secrets
        return True

    async def parse_webhook(self, headers: Dict[str, str], body: bytes) -> WebhookResult:
        data = json.loads(body.decode("utf-8"))
        event = data.get("event")
        payment_obj = data.get("object", {})

        order_id = payment_obj.get("metadata", {}).get("order_id", "")
        if not order_id:
            order_id = payment_obj.get("id", "")

        is_paid = event == "payment.succeeded" or payment_obj.get("status") == "succeeded"
        amount_val = float(payment_obj.get("amount", {}).get("value", 0.0))

        return WebhookResult(
            order_id=order_id,
            is_paid=is_paid,
            external_invoice_id=payment_obj.get("id"),
            amount_paid=amount_val,
            currency="RUB",
            raw_event=data,
        )
