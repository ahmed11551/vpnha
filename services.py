"""
Business logic and service layer for NexusVPN ecosystem.
Centralizes:
- User lifecycle & referral attribution (shared between FastAPI and Bot)
- Payment invoice generation & signature-verified webhook processing (CryptoBot / Telegram Stars)
- Automated referral commissions
- Telegram notification dispatch
- Background subscription monitors
"""

import hashlib
import hmac
import json
import logging
import os
import secrets
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import httpx
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models import PaymentTransaction, Referral, Subscription, User
from marzban_client import marzban_client

logger = logging.getLogger("NexusVPN-Services")

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
CRYPTO_BOT_TOKEN = os.getenv("CRYPTO_BOT_TOKEN", "")
CRYPTO_BOT_NET = os.getenv("CRYPTO_BOT_NET", "mainnet")  # mainnet or testnet
REFERRAL_BONUS_RUB = float(os.getenv("REFERRAL_BONUS_RUB", "100.0"))
REFERRAL_PERCENT = float(os.getenv("REFERRAL_COMMISSION_PERCENT", "15.0"))


# --------------------------------------------------------------------------
# User & Referral Service
# --------------------------------------------------------------------------

async def get_or_create_user(
    db: AsyncSession,
    telegram_id: int,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
    ref_code_arg: Optional[str] = None,
) -> Tuple[User, bool]:
    """
    Find user by telegram_id or create new one with unique ref_code & inviter link.
    Returns: (User, created: bool)
    """
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user:
        updated = False
        if username and user.username != username:
            user.username = username
            updated = True
        if first_name and user.first_name != first_name:
            user.first_name = first_name
            updated = True
        if updated:
            await db.commit()
            await db.refresh(user)
        return user, False

    # Generate unique referral code
    new_ref_code = secrets.token_hex(4).upper()
    while True:
        check_stmt = select(User).where(User.ref_code == new_ref_code)
        exists = (await db.execute(check_stmt)).scalar_one_or_none()
        if not exists:
            break
        new_ref_code = secrets.token_hex(4).upper()

    marz_username = f"tg_{telegram_id}_{new_ref_code.lower()}"

    # Handle inviter referral link
    inviter_id = None
    if ref_code_arg:
        cleaned_ref = ref_code_arg.replace("ref_", "").strip().upper()
        inviter_stmt = select(User).where(User.ref_code == cleaned_ref)
        inviter_res = await db.execute(inviter_stmt)
        inviter = inviter_res.scalar_one_or_none()
        if inviter and inviter.telegram_id != telegram_id:
            inviter_id = inviter.id
            logger.info("New user %s invited by user %s (ref: %s)", telegram_id, inviter.telegram_id, cleaned_ref)

    new_user = User(
        telegram_id=telegram_id,
        username=username,
        first_name=first_name,
        balance=0.0,
        ref_code=new_ref_code,
        invited_by=inviter_id,
        free_trial_used=False,
        marzban_username=marz_username,
        created_at=datetime.utcnow(),
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    # If invited, create pending Referral record
    if inviter_id:
        referral_record = Referral(
            referrer_id=inviter_id,
            referee_id=new_user.id,
            reward_amount=0.0,
            is_paid=False,
            created_at=datetime.utcnow(),
        )
        db.add(referral_record)
        await db.commit()

    logger.info("Created new user: tg_id=%s, ref_code=%s", telegram_id, new_ref_code)
    return new_user, True


async def award_referral_bonus_on_purchase(
    db: AsyncSession,
    user: User,
    purchase_amount: float,
    bot_token: Optional[str] = None,
) -> float:
    """
    Awards referral commission to the inviter when user completes a purchase.
    """
    if not user.invited_by:
        return 0.0

    ref_stmt = select(Referral).where(
        Referral.referrer_id == user.invited_by,
        Referral.referee_id == user.id,
        Referral.is_paid == False,
    )
    ref_res = await db.execute(ref_stmt)
    referral_record = ref_res.scalar_one_or_none()

    if not referral_record:
        return 0.0

    bonus = max(REFERRAL_BONUS_RUB, purchase_amount * (REFERRAL_PERCENT / 100.0))
    bonus = round(bonus, 2)
    referral_record.reward_amount = bonus
    referral_record.is_paid = True

    inviter_stmt = select(User).where(User.id == user.invited_by)
    inviter = (await db.execute(inviter_stmt)).scalar_one_or_none()

    if inviter:
        inviter.balance += bonus
        await db.commit()
        logger.info("Awarded referral bonus %.2f RUB to inviter %s", bonus, inviter.telegram_id)

        # Notify inviter via Telegram bot
        token_to_use = bot_token or BOT_TOKEN
        if token_to_use:
            msg = (
                f"🎉 <b>Вам начислен реферальный бонус!</b>\n\n"
                f"Ваш реферал совершил оплату. На ваш баланс зачислено: <b>+{bonus:.2f} ₽</b>.\n"
                f"Текущий баланс: <b>{inviter.balance:.2f} ₽</b>."
            )
            await send_telegram_message(inviter.telegram_id, msg, token_to_use)

    return bonus


# --------------------------------------------------------------------------
# Telegram Notifications
# --------------------------------------------------------------------------

async def send_telegram_message(telegram_id: int, text: str, bot_token: Optional[str] = None) -> bool:
    """Sends HTML notification directly to user via Telegram Bot API."""
    token = bot_token or BOT_TOKEN
    if not token or token.startswith("123456789:ABC"):
        logger.info("Skipping Telegram message (bot token not configured): %s", text[:40])
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": telegram_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=payload)
            return resp.status_code == 200
    except Exception as exc:
        logger.warning("Failed to send telegram message to %s: %s", telegram_id, exc)
        return False


# --------------------------------------------------------------------------
# Payment Gateway Services: CryptoBot & Telegram Stars
# --------------------------------------------------------------------------

async def create_crypto_bot_invoice(
    amount_rub: float,
    order_id: str,
    description: str = "Пополнение баланса NexusVPN",
) -> Dict[str, Any]:
    """
    Creates an official invoice on @CryptoBot (Crypto Pay API).
    Docs: https://help.crypt.bot/crypto-pay-api
    """
    token = os.getenv("CRYPTO_BOT_TOKEN", "").strip()
    base_api = "https://pay.crypt.bot/api" if CRYPTO_BOT_NET == "mainnet" else "https://testnet-pay.crypt.bot/api"

    if not token:
        # Return fallback demo invoice link
        return {
            "invoice_id": f"demo_{order_id}",
            "pay_url": f"https://t.me/CryptoBot?start=invoice_{order_id}",
            "amount": amount_rub,
            "currency": "RUB",
            "is_mock": True,
        }

    url = f"{base_api}/createInvoice"
    headers = {"Crypto-Pay-API-Token": token}
    payload = {
        "currency_type": "fiat",
        "fiat": "RUB",
        "amount": f"{amount_rub:.2f}",
        "description": description,
        "payload": order_id,
        "paid_btn_name": "callback",
        "paid_btn_url": f"https://t.me/{os.getenv('BOT_USERNAME', 'NexusVpnBot')}",
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            data = resp.json()
            if data.get("ok"):
                result = data.get("result", {})
                return {
                    "invoice_id": str(result.get("invoice_id")),
                    "pay_url": result.get("bot_invoice_url") or result.get("mini_app_invoice_url") or result.get("web_app_invoice_url"),
                    "amount": amount_rub,
                    "currency": "RUB",
                    "is_mock": False,
                }
            logger.error("CryptoBot createInvoice error: %s", data)
    except Exception as exc:
        logger.error("CryptoBot connection error: %s", exc)

    return {
        "invoice_id": f"fallback_{order_id}",
        "pay_url": f"https://t.me/CryptoBot?start={order_id}",
        "amount": amount_rub,
        "currency": "RUB",
        "is_mock": True,
    }


def verify_crypto_bot_webhook(raw_body: bytes, signature: str, token: str) -> bool:
    """
    Verifies @CryptoBot webhook signature:
    HMAC-SHA256 of raw body with SHA256(token) as secret key.
    """
    if not token or not signature:
        return False

    secret_key = hashlib.sha256(token.encode("utf-8")).digest()
    calculated_signature = hmac.new(secret_key, raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(calculated_signature, signature)


async def process_successful_payment(
    db: AsyncSession,
    order_id: str,
    gateway: str,
    external_id: Optional[str] = None,
) -> Optional[PaymentTransaction]:
    """
    Safely and idempotently credits user balance and marks transaction as paid.
    """
    stmt = select(PaymentTransaction).where(PaymentTransaction.order_id == order_id)
    tx = (await db.execute(stmt)).scalar_one_or_none()

    if not tx:
        logger.error("Payment transaction not found for order_id: %s", order_id)
        return None

    # Idempotency check: if already processed, return existing
    if tx.status == "paid":
        logger.info("Order %s already processed (idempotent skipped)", order_id)
        return tx

    tx.status = "paid"
    tx.paid_at = datetime.utcnow()
    if external_id:
        tx.external_invoice_id = external_id

    # Credit user balance
    user_stmt = select(User).where(User.id == tx.user_id)
    user = (await db.execute(user_stmt)).scalar_one_or_none()
    if user:
        user.balance += tx.amount
        await db.commit()
        await db.refresh(tx)
        await db.refresh(user)

        logger.info("Payment confirmed! User %s credited with %.2f %s. New balance: %.2f",
                    user.telegram_id, tx.amount, tx.currency, user.balance)

        # Send push notification
        msg = (
            f"✅ <b>Баланс успешно пополнен!</b>\n\n"
            f"Сумма: <b>+{tx.amount:.2f} ₽</b> ({gateway.upper()})\n"
            f"Текущий баланс: <b>{user.balance:.2f} ₽</b>\n\n"
            f"Теперь вы можете оформить или продлить подписку в меню бота или Mini App."
        )
        await send_telegram_message(user.telegram_id, msg)

    return tx


# --------------------------------------------------------------------------
# Background Monitor for Expiring Subscriptions
# --------------------------------------------------------------------------

async def check_expiring_subscriptions(db: AsyncSession) -> int:
    """
    Checks for subscriptions expiring in less than 24 hours and sends renewal reminders.
    """
    now = datetime.utcnow()
    target_window = now + timedelta(hours=24)

    stmt = (
        select(Subscription, User)
        .join(User, Subscription.user_id == User.id)
        .where(
            Subscription.is_active == True,
            Subscription.end_date > now,
            Subscription.end_date <= target_window,
        )
    )
    results = (await db.execute(stmt)).all()
    count = 0

    for sub, user in results:
        hours_left = max(1, int((sub.end_date - now).total_seconds() / 3600))
        msg = (
            f"⚠️ <b>Внимание! Ваша подписка NexusVPN истекает через {hours_left} ч.</b>\n\n"
            f"Тариф: <b>{sub.plan_name}</b>\n"
            f"Окончание: <b>{sub.end_date.strftime('%d.%m.%Y %H:%M')}</b>\n\n"
            f"Чтобы избежать перебоев в работе VPN, пожалуйста, продлите подписку в Mini App!"
        )
        await send_telegram_message(user.telegram_id, msg)
        count += 1

    return count
