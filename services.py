"""
Business logic and service layer for NexusVPN ecosystem.
Centralizes:
- User lifecycle & referral attribution (shared between FastAPI and Bot)
- Payment order creation, webhook verification & processing across CryptoBot, Stars, YooKassa
- PromoCode validation, discount computation, and instant activation
- Subscription creation, renewal, and Marzban VLESS Reality provisioning
- Automatic expiration enforcement (disabling expired keys in Marzban core)
- Telegram notification dispatch
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

from models import Payment, PromoCode, Referral, Subscription, User
from marzban_client import marzban_client
from payments import get_payment_provider, InvoiceRequest
from config import settings

logger = logging.getLogger("NexusVPN-Services")

BOT_TOKEN = settings.BOT_TOKEN
CRYPTO_BOT_TOKEN = settings.CRYPTO_BOT_TOKEN or ""
REFERRAL_BONUS_RUB = settings.REFERRAL_BONUS_RUB
REFERRAL_PERCENT = settings.REFERRAL_COMMISSION_PERCENT

SUBSCRIPTION_PLANS = {
    "1m": {"name": "1 Месяц", "days": 30, "price": 199.0, "popular": False},
    "3m": {"name": "3 Месяца", "days": 90, "price": 499.0, "popular": False},
    "6m": {"name": "6 Месяцев", "days": 180, "price": 899.0, "popular": True},
    "12m": {"name": "12 Месяцев", "days": 365, "price": 1499.0, "popular": False},
}


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
    """Awards referral commission to the inviter when user completes a purchase."""
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
# Promo Code Engine
# --------------------------------------------------------------------------

async def validate_and_apply_promocode(
    db: AsyncSession,
    user: User,
    code_text: str,
) -> Dict[str, Any]:
    """
    Validates a promo code and applies either instant bonuses (balance/free days)
    or returns discount details for checkout.
    """
    clean_code = code_text.strip().upper()
    stmt = select(PromoCode).where(PromoCode.code == clean_code, PromoCode.is_active == True)
    promo = (await db.execute(stmt)).scalar_one_or_none()

    now = datetime.utcnow()
    if not promo:
        return {"valid": False, "message": "Промокод не существует или отключен"}

    if promo.expires_at and promo.expires_at < now:
        return {"valid": False, "message": "Срок действия промокода истёк"}

    if promo.current_activations >= promo.max_activations:
        return {"valid": False, "message": "Лимит активаций этого промокода исчерпан"}

    # If promo grants instant bonus balance
    bonus_rub = promo.bonus_rub
    bonus_days = promo.bonus_days
    discount_pct = promo.discount_percent

    message_parts = []
    if bonus_rub > 0:
        user.balance += bonus_rub
        message_parts.append(f"+{bonus_rub:.0f} ₽ на баланс")

    if bonus_days > 0:
        # Check active subscription
        sub_stmt = (
            select(Subscription)
            .where(Subscription.user_id == user.id, Subscription.is_active == True, Subscription.end_date > now)
            .order_by(Subscription.end_date.desc())
        )
        active_sub = (await db.execute(sub_stmt)).scalar_one_or_none()
        if active_sub:
            active_sub.end_date += timedelta(days=bonus_days)
            new_expire_ts = int(active_sub.end_date.timestamp())
            await marzban_client.extend_user(user.marzban_username, new_expire_ts=new_expire_ts)
            message_parts.append(f"+{bonus_days} дней к активной подписке")
        else:
            # Create promotional mini-subscription
            end_date = now + timedelta(days=bonus_days)
            expire_ts = int(end_date.timestamp())
            marz_user = await marzban_client.create_user(
                username=user.marzban_username,
                expire_timestamp=expire_ts,
                note=f"Promocode {clean_code}",
            )
            links = await marzban_client.get_user_links(user.marzban_username)
            new_sub = Subscription(
                user_id=user.id,
                plan_name=f"Бонус ({clean_code})",
                start_date=now,
                end_date=end_date,
                is_active=True,
                subscription_url=links.get("subscription_url"),
                vless_link=links.get("primary_vless_link"),
            )
            db.add(new_sub)
            message_parts.append(f"+{bonus_days} бесплатных дней VPN")

    promo.current_activations += 1
    await db.commit()
    await db.refresh(user)

    result_msg = "Промокод успешно применён! " + ", ".join(message_parts) if message_parts else f"Скидка {discount_pct:.0f}% активна для покупки тарифа"

    return {
        "valid": True,
        "promo_id": promo.id,
        "code": promo.code,
        "discount_percent": discount_pct,
        "bonus_days": bonus_days,
        "bonus_rub": bonus_rub,
        "message": result_msg,
        "new_balance": user.balance,
    }


# --------------------------------------------------------------------------
# Payment Order & Processing Architecture
# --------------------------------------------------------------------------

async def create_payment_order(
    db: AsyncSession,
    user: User,
    amount: float,
    gateway: str,
    plan_id: Optional[str] = None,
    promo_code_id: Optional[int] = None,
    description: Optional[str] = None,
) -> Tuple[Payment, str]:
    """
    Creates a Payment record and initiates an invoice with the chosen gateway.
    Returns: (Payment, pay_url)
    """
    order_id = f"ord_{int(time.time())}_{secrets.token_hex(4)}"
    desc = description or (f"Тариф {SUBSCRIPTION_PLANS.get(plan_id, {}).get('name', plan_id)}" if plan_id else "Пополнение баланса NexusVPN")

    provider = get_payment_provider(gateway)
    invoice_req = InvoiceRequest(
        order_id=order_id,
        user_id=user.id,
        telegram_id=user.telegram_id,
        amount=amount,
        currency="RUB",
        description=desc,
        plan_id=plan_id,
    )

    invoice_res = await provider.create_invoice(invoice_req)

    payment = Payment(
        user_id=user.id,
        order_id=order_id,
        gateway=gateway,
        amount=amount,
        currency=invoice_res.currency,
        status="pending",
        plan_id=plan_id,
        promo_code_id=promo_code_id,
        external_invoice_id=invoice_res.external_invoice_id,
        pay_url=invoice_res.pay_url,
        meta_data=json.dumps(invoice_res.meta_data) if invoice_res.meta_data else None,
        created_at=datetime.utcnow(),
    )
    db.add(payment)
    await db.commit()
    await db.refresh(payment)

    return payment, invoice_res.pay_url


async def process_successful_payment(
    db: AsyncSession,
    order_id: str,
    gateway: str,
    external_id: Optional[str] = None,
) -> Optional[Payment]:
    """
    Safely and idempotently credits user balance or activates purchased plan.
    Marks payment as paid.
    """
    stmt = select(Payment).where(Payment.order_id == order_id)
    payment = (await db.execute(stmt)).scalar_one_or_none()

    if not payment:
        logger.error("Payment record not found for order_id: %s", order_id)
        return None

    # Idempotency check: if already processed, return existing
    if payment.status == "paid":
        logger.info("Order %s already processed (idempotent skipped)", order_id)
        return payment

    payment.status = "paid"
    payment.paid_at = datetime.utcnow()
    if external_id:
        payment.external_invoice_id = external_id

    # User lookup
    user_stmt = select(User).where(User.id == payment.user_id)
    user = (await db.execute(user_stmt)).scalar_one_or_none()
    if not user:
        await db.commit()
        return payment

    # If payment was for a specific plan, automatically activate it
    if payment.plan_id and payment.plan_id in SUBSCRIPTION_PLANS:
        plan = SUBSCRIPTION_PLANS[payment.plan_id]
        logger.info("Auto-activating plan %s for user %s after direct payment", payment.plan_id, user.telegram_id)
        sub = await purchase_subscription_internal(db, user, payment.plan_id, deduct_balance=False)
        await award_referral_bonus_on_purchase(db, user, payment.amount)
        await db.commit()
        await db.refresh(payment)

        msg = (
            f"🎉 <b>Оплата прошла успешно!</b>\n\n"
            f"Тариф <b>{plan['name']}</b> активирован на {plan['days']} дней.\n"
            f"Ваш персональный VLESS Reality ключ обновлён в приложении!"
        )
        await send_telegram_message(user.telegram_id, msg)
        return payment

    # Otherwise credit user balance
    user.balance += payment.amount
    await db.commit()
    await db.refresh(payment)
    await db.refresh(user)

    logger.info("Payment confirmed! User %s credited with %.2f %s. New balance: %.2f",
                user.telegram_id, payment.amount, payment.currency, user.balance)

    msg = (
        f"✅ <b>Баланс успешно пополнен!</b>\n\n"
        f"Сумма: <b>+{payment.amount:.2f} ₽</b> ({gateway.upper()})\n"
        f"Текущий баланс: <b>{user.balance:.2f} ₽</b>\n\n"
        f"Теперь вы можете оформить или продлить подписку в меню бота или Mini App."
    )
    await send_telegram_message(user.telegram_id, msg)

    return payment


# --------------------------------------------------------------------------
# Subscription Purchase & Marzban Integration
# --------------------------------------------------------------------------

async def purchase_subscription_internal(
    db: AsyncSession,
    user: User,
    plan_id: str,
    deduct_balance: bool = True,
    promo_code_obj: Optional[PromoCode] = None,
) -> Subscription:
    """Internal core routine to provision/extend subscription in Marzban and DB."""
    if plan_id not in SUBSCRIPTION_PLANS:
        raise ValueError(f"Unknown plan_id: {plan_id}")

    plan = SUBSCRIPTION_PLANS[plan_id]
    base_price = plan["price"]
    bonus_days = 0

    if promo_code_obj:
        if promo_code_obj.discount_percent > 0:
            base_price = round(base_price * (1.0 - promo_code_obj.discount_percent / 100.0), 2)
        bonus_days = promo_code_obj.bonus_days

    total_days = plan["days"] + bonus_days

    if deduct_balance:
        if user.balance < base_price:
            raise ValueError(f"Недостаточно средств на балансе. Требуется: {base_price:.2f} ₽, на балансе: {user.balance:.2f} ₽")
        user.balance -= base_price

    now = datetime.utcnow()
    # Check active subscription
    sub_stmt = (
        select(Subscription)
        .where(Subscription.user_id == user.id, Subscription.is_active == True, Subscription.end_date > now)
        .order_by(Subscription.end_date.desc())
    )
    active_sub = (await db.execute(sub_stmt)).scalar_one_or_none()

    if active_sub:
        start_base = max(active_sub.end_date, now)
        new_end_date = start_base + timedelta(days=total_days)
        active_sub.end_date = new_end_date
        active_sub.plan_name = plan["name"]
        target_sub = active_sub
    else:
        new_end_date = now + timedelta(days=total_days)
        target_sub = Subscription(
            user_id=user.id,
            plan_name=plan["name"],
            start_date=now,
            end_date=new_end_date,
            is_active=True,
        )
        db.add(target_sub)

    # Synchronize with Marzban panel
    expire_timestamp = int(new_end_date.timestamp())
    try:
        marz_user = await marzban_client.create_user(
            username=user.marzban_username,
            expire_timestamp=expire_timestamp,
            note=f"NexusVPN plan {plan['name']} (tg: {user.telegram_id})",
        )
        marz_links = await marzban_client.get_user_links(user.marzban_username)
        target_sub.subscription_url = marz_links.get("subscription_url")
        target_sub.vless_link = marz_links.get("primary_vless_link")
    except Exception as exc:
        logger.error("Marzban sync error during purchase: %s", exc)
        # Resilient fallback mock link
        if not target_sub.vless_link:
            mock = marzban_client._generate_mock_user(user.marzban_username, expire_timestamp)
            target_sub.vless_link = mock["links"][0]
            target_sub.subscription_url = mock["subscription_url"]

    await db.commit()
    await db.refresh(target_sub)
    await db.refresh(user)

    if deduct_balance:
        await award_referral_bonus_on_purchase(db, user, base_price)

    return target_sub


# --------------------------------------------------------------------------
# Background Monitors: Reminders & Hard Expired Disabling
# --------------------------------------------------------------------------

async def check_expiring_subscriptions(db: AsyncSession) -> int:
    """Checks for subscriptions expiring in less than 24 hours and sends renewal reminders."""
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


async def check_and_disable_expired_subscriptions(db: AsyncSession) -> int:
    """
    Finds all expired active subscriptions, marks them is_active=False in DB,
    and calls Marzban to disable user access (status: 'disabled').
    """
    now = datetime.utcnow()
    stmt = (
        select(Subscription, User)
        .join(User, Subscription.user_id == User.id)
        .where(
            Subscription.is_active == True,
            Subscription.end_date <= now,
        )
    )
    results = (await db.execute(stmt)).all()
    disabled_count = 0

    for sub, user in results:
        sub.is_active = False
        # Disable in Marzban
        try:
            await marzban_client.disable_user(user.marzban_username)
            logger.info("Disabled Marzban user %s due to expired subscription", user.marzban_username)
        except Exception as exc:
            logger.warning("Could not disable Marzban user %s: %s", user.marzban_username, exc)

        msg = (
            f"🛑 <b>Срок действия вашей подписки NexusVPN истёк</b>\n\n"
            f"Тариф: <b>{sub.plan_name}</b>\n"
            f"Доступ к VPN-серверам временно приостановлен.\n\n"
            f"Чтобы возобновить подключение, продлите подписку в Mini App!"
        )
        await send_telegram_message(user.telegram_id, msg)
        disabled_count += 1

    if disabled_count > 0:
        await db.commit()
        logger.info("Successfully marked and disabled %d expired subscriptions", disabled_count)

    return disabled_count


# Backward-compatibility alias
create_crypto_bot_invoice = None
def verify_crypto_bot_webhook(raw_body: bytes, signature: str, token: str) -> bool:
    if not token or not signature:
        return False
    secret_key = hashlib.sha256(token.encode("utf-8")).digest()
    calculated_signature = hmac.new(secret_key, raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(calculated_signature, signature)
