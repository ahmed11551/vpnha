"""
Telegram Stars Payment Provider.
Supports in-app Telegram Stars (XTR) payments using createInvoiceLink API.
"""

import json
import logging
import os
import uuid
from typing import Any, Dict, Optional
import httpx
from payments.base import BasePaymentProvider, InvoiceRequest, InvoiceResult, WebhookResult

logger = logging.getLogger("TelegramStarsProvider")

# Approx conversion: 1 Star = 1.95 RUB
RUB_PER_STAR = float(os.getenv("RUB_PER_STAR", "1.95"))


class TelegramStarsProvider(BasePaymentProvider):
    gateway_name = "stars"

    def __init__(self, bot_token: Optional[str] = None):
        self.bot_token = (bot_token or os.getenv("BOT_TOKEN", "")).strip()

    async def create_invoice(self, request: InvoiceRequest) -> InvoiceResult:
        """Create a Telegram Stars invoice link via Telegram Bot API."""
        stars_amount = max(1, int(round(request.amount / RUB_PER_STAR)))

        if not self.bot_token or ":" not in self.bot_token:
            logger.info("Bot token not configured or sandbox mode. Returning mock Stars link.")
            mock_id = f"stars_{uuid.uuid4().hex[:10]}"
            return InvoiceResult(
                order_id=request.order_id,
                external_invoice_id=mock_id,
                pay_url=f"https://t.me/NexusVpnBot?start=stars_{request.order_id}",
                amount=request.amount,
                currency="XTR",
                gateway=self.gateway_name,
                meta_data={"stars": stars_amount, "sandbox": True},
            )

        url = f"https://api.telegram.org/bot{self.bot_token}/createInvoiceLink"
        payload = {
            "title": "NexusVPN Подписка",
            "description": request.description,
            "payload": json.dumps({"order_id": request.order_id, "user_id": request.user_id}),
            "currency": "XTR",
            "prices": [{"label": f"{request.description} ({stars_amount} ⭐)", "amount": stars_amount}],
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(url, json=payload)
                data = resp.json()
                if data.get("ok"):
                    invoice_link = data["result"]
                    return InvoiceResult(
                        order_id=request.order_id,
                        external_invoice_id=f"stars_{request.order_id}",
                        pay_url=invoice_link,
                        amount=request.amount,
                        currency="XTR",
                        gateway=self.gateway_name,
                        meta_data={"stars": stars_amount, "invoice_link": invoice_link},
                    )
                else:
                    logger.warning("Telegram createInvoiceLink returned error: %s", data)
                    raise Exception(data.get("description", "Failed to create invoice link"))
        except Exception as exc:
            logger.warning("Error calling Telegram Stars API (%s), returning fallback link", exc)
            return InvoiceResult(
                order_id=request.order_id,
                external_invoice_id=f"stars_{request.order_id}",
                pay_url=f"https://t.me/NexusVpnBot?start=stars_{request.order_id}",
                amount=request.amount,
                currency="XTR",
                gateway=self.gateway_name,
                meta_data={"fallback": True, "stars": stars_amount, "error": str(exc)},
            )

    async def verify_webhook(self, headers: Dict[str, str], body: bytes) -> bool:
        # Telegram updates are signed by Telegram secret token if configured
        secret = os.getenv("TELEGRAM_WEBHOOK_SECRET")
        if secret:
            header_secret = headers.get("X-Telegram-Bot-Api-Secret-Token") or headers.get("x-telegram-bot-api-secret-token")
            return header_secret == secret
        return True

    async def parse_webhook(self, headers: Dict[str, str], body: bytes) -> WebhookResult:
        data = json.loads(body.decode("utf-8"))
        pre_checkout = data.get("pre_checkout_query")
        successful_payment = None

        if "message" in data and "successful_payment" in data["message"]:
            successful_payment = data["message"]["successful_payment"]

        order_id = ""
        amount = 0.0

        if successful_payment:
            raw_payload = successful_payment.get("invoice_payload", "")
            try:
                parsed = json.loads(raw_payload) if isinstance(raw_payload, str) else raw_payload
                order_id = parsed.get("order_id", "")
            except Exception:
                order_id = str(raw_payload)
            amount = float(successful_payment.get("total_amount", 0)) * RUB_PER_STAR
            return WebhookResult(
                order_id=order_id,
                is_paid=True,
                external_invoice_id=successful_payment.get("telegram_payment_charge_id"),
                amount_paid=amount,
                currency="XTR",
                raw_event=data,
            )

        return WebhookResult(
            order_id=order_id,
            is_paid=False,
            raw_event=data,
        )
