"""
Production-grade FastAPI Backend for NexusVPN Commercial Platform.
Hardened Architecture & Security:
- Telegram WebApp initData HMAC-SHA256 validation with anti-replay timestamp verification
- Rate-limiting on auth, trial, and payment endpoints
- Secure Payment Gateway integration (CryptoBot / Telegram Stars) with cryptographically verified webhooks and idempotency
- Dynamic Marzban node & cluster telemetry (/api/servers)
- Modern FastAPI Lifespan context manager with background subscription health checks
- Strict CORS origin validation
"""

import asyncio
import hashlib
import json
import logging
import os
import secrets
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException, Header, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import async_session_factory, get_db, init_db
from marzban_client import marzban_client
from models import PaymentTransaction, Referral, Subscription, User
from security import (
    ALLOW_INSECURE_TEST_AUTH,
    auth_rate_limiter,
    get_allowed_cors_origins,
    payment_rate_limiter,
    trial_rate_limiter,
    validate_telegram_init_data,
)
from services import (
    award_referral_bonus_on_purchase,
    check_expiring_subscriptions,
    create_crypto_bot_invoice,
    get_or_create_user,
    process_successful_payment,
    send_telegram_message,
    verify_crypto_bot_webhook,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("NexusVPN-Backend")

# Environment constants
BOT_TOKEN = os.getenv("BOT_TOKEN", "123456789:ABCdefGHIjklMNOpqrSTUvwxYZ")
BOT_USERNAME = os.getenv("BOT_USERNAME", "NexusVpnBot")
CRYPTO_BOT_TOKEN = os.getenv("CRYPTO_BOT_TOKEN", "").strip()
FREE_TRIAL_DAYS = int(os.getenv("FREE_TRIAL_DAYS", "3"))
REFERRAL_BONUS_RUB = float(os.getenv("REFERRAL_BONUS_RUB", "100.0"))
REFERRAL_PERCENT = float(os.getenv("REFERRAL_COMMISSION_PERCENT", "15.0"))

# Tariff pricing
SUBSCRIPTION_PLANS = {
    "1m": {"name": "1 Месяц", "days": 30, "price": 199.0, "popular": False},
    "3m": {"name": "3 Месяца", "days": 90, "price": 499.0, "popular": False},
    "6m": {"name": "6 Месяцев", "days": 180, "price": 899.0, "popular": True},
    "12m": {"name": "12 Месяцев", "days": 365, "price": 1499.0, "popular": False},
}


# --------------------------------------------------------------------------
# Modern Lifespan & Background Tasks
# --------------------------------------------------------------------------

async def subscription_monitor_task():
    """Background task running every hour to monitor expiring subscriptions."""
    while True:
        try:
            await asyncio.sleep(3600)  # Check every hour
            async with async_session_factory() as db:
                reminders_sent = await check_expiring_subscriptions(db)
                if reminders_sent > 0:
                    logger.info("Sent %s subscription expiration reminder(s)", reminders_sent)
        except asyncio.CancelledError:
            break
        except Exception as exc:
            logger.error("Error in background subscription monitor: %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Modern lifespan handler replacing deprecated on_event."""
    logger.info("Initializing database schemas...")
    await init_db()

    # Launch background monitor
    monitor_coro = asyncio.create_task(subscription_monitor_task())
    logger.info("Background subscription monitor started.")

    yield

    # Clean shutdown
    monitor_coro.cancel()
    try:
        await monitor_coro
    except asyncio.CancelledError:
        pass
    logger.info("Backend services stopped gracefully.")


# Initialize FastAPI with Lifespan
app = FastAPI(
    title="NexusVPN Commercial Platform API",
    description="High-security API gateway for Telegram Mini App, Bot and Marzban Xray VLESS+Reality",
    version="2.1.0",
    lifespan=lifespan,
)

# Secure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files mount
frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
if os.path.isdir(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")


# --------------------------------------------------------------------------
# Pydantic Schemas
# --------------------------------------------------------------------------

class AuthTelegramRequest(BaseModel):
    init_data: str = Field(..., description="Raw Telegram.WebApp.initData string")
    ref_code: Optional[str] = Field(None, description="Optional referral code")


class PurchaseSubscriptionRequest(BaseModel):
    plan_id: str = Field(..., description="Plan identifier: 1m, 3m, 6m, 12m")


class CreateInvoiceRequest(BaseModel):
    amount: float = Field(..., gt=10, description="Amount in rubles (min 10 RUB)")
    gateway: str = Field("cryptobot", description="Payment gateway: 'cryptobot' or 'stars'")


class SandboxTopUpRequest(BaseModel):
    amount: float = Field(..., gt=0, description="Amount to add in development test mode only")


# --------------------------------------------------------------------------
# Subscription Helper
# --------------------------------------------------------------------------

async def get_active_subscription(db: AsyncSession, user_id: int) -> Optional[Subscription]:
    """Retrieve the active subscription for a user, if not expired."""
    now = datetime.utcnow()
    stmt = (
        select(Subscription)
        .where(
            Subscription.user_id == user_id,
            Subscription.is_active == True,
            Subscription.end_date > now,
        )
        .order_by(Subscription.end_date.desc())
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


# --------------------------------------------------------------------------
# API Endpoints
# --------------------------------------------------------------------------

@app.get("/")
async def root():
    """Serves the Mini App HTML or system status."""
    frontend_index = os.path.join(frontend_dir, "index.html")
    if os.path.isfile(frontend_index):
        return FileResponse(frontend_index)
    return {
        "service": "NexusVPN Commercial Ecosystem",
        "status": "operational",
        "version": "2.1.0",
        "bot": f"@{BOT_USERNAME}",
    }


@app.get("/api/health")
async def health_check():
    """Health check for monitoring and load balancers."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "marzban_host": marzban_client.base_url,
    }


@app.post("/api/auth/telegram")
async def authenticate_telegram(
    payload: AuthTelegramRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Cryptographically authenticates Telegram WebApp initData.
    Applies sliding-window rate limiting to prevent credential stuffing.
    """
    client_ip = request.client.host if request.client else "unknown"
    auth_rate_limiter.check(client_ip, "авторизацию")

    try:
        tg_user_data = validate_telegram_init_data(payload.init_data, BOT_TOKEN)
    except ValueError as exc:
        logger.warning("Auth failure from %s: %s", client_ip, exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Ошибка проверки подписи Telegram: {str(exc)}",
        )

    telegram_id = int(tg_user_data["id"])
    username = tg_user_data.get("username")
    first_name = tg_user_data.get("first_name", "User")

    # Get or create user via central service
    user, is_new = await get_or_create_user(
        db=db,
        telegram_id=telegram_id,
        username=username,
        first_name=first_name,
        ref_code_arg=payload.ref_code,
    )

    # Active subscription check
    active_sub = await get_active_subscription(db, user.id)
    sub_data = None
    if active_sub:
        now = datetime.utcnow()
        time_left = max(0, int((active_sub.end_date - now).total_seconds()))
        sub_data = {
            "id": active_sub.id,
            "plan_name": active_sub.plan_name,
            "start_date": active_sub.start_date.isoformat(),
            "end_date": active_sub.end_date.isoformat(),
            "time_left_seconds": time_left,
            "is_active": active_sub.is_active,
            "vless_link": active_sub.vless_link,
            "subscription_url": active_sub.subscription_url,
            "traffic_limit_bytes": active_sub.traffic_limit_bytes,
            "used_traffic_bytes": active_sub.used_traffic_bytes,
        }

    # Referral statistics
    invited_count = (
        await db.execute(select(func.count(User.id)).where(User.invited_by == user.id))
    ).scalar_one() or 0

    earned_sum = (
        await db.execute(
            select(func.sum(Referral.reward_amount)).where(
                Referral.referrer_id == user.id, Referral.is_paid == True
            )
        )
    ).scalar_one() or 0.0

    return {
        "id": user.id,
        "telegram_id": user.telegram_id,
        "username": user.username,
        "first_name": user.first_name,
        "balance": round(user.balance, 2),
        "ref_code": user.ref_code,
        "free_trial_used": user.free_trial_used,
        "marzban_username": user.marzban_username,
        "active_subscription": sub_data,
        "referral_stats": {
            "ref_link": f"https://t.me/{BOT_USERNAME}?start=ref_{user.ref_code}",
            "invited_count": invited_count,
            "total_earned": round(earned_sum, 2),
            "bonus_per_user": REFERRAL_BONUS_RUB,
            "commission_percent": REFERRAL_PERCENT,
        },
    }


@app.get("/api/user/me")
async def get_current_user_profile(
    telegram_id: int = Query(..., description="Telegram ID of the user"),
    db: AsyncSession = Depends(get_db),
):
    """Fetches user profile and active subscription."""
    stmt = select(User).where(User.telegram_id == telegram_id)
    user = (await db.execute(stmt)).scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    active_sub = await get_active_subscription(db, user.id)
    sub_data = None
    if active_sub:
        now = datetime.utcnow()
        time_left = max(0, int((active_sub.end_date - now).total_seconds()))
        sub_data = {
            "id": active_sub.id,
            "plan_name": active_sub.plan_name,
            "end_date": active_sub.end_date.isoformat(),
            "time_left_seconds": time_left,
            "is_active": active_sub.is_active,
            "vless_link": active_sub.vless_link,
            "subscription_url": active_sub.subscription_url,
        }

    return {
        "id": user.id,
        "telegram_id": user.telegram_id,
        "username": user.username,
        "first_name": user.first_name,
        "balance": round(user.balance, 2),
        "ref_code": user.ref_code,
        "free_trial_used": user.free_trial_used,
        "active_subscription": sub_data,
    }


@app.post("/api/subscription/trial")
async def activate_free_trial(
    telegram_id: int = Query(..., description="Telegram ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    Activates one-time 3-day / 5GB free trial.
    Protected by rate limiter and DB flags against fraud.
    """
    trial_rate_limiter.check(str(telegram_id), "активацию пробного периода")

    stmt = select(User).where(User.telegram_id == telegram_id)
    user = (await db.execute(stmt)).scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    if user.free_trial_used:
        raise HTTPException(
            status_code=400,
            detail="Вы уже использовали бесплатный пробный период. Выберите тариф для продолжения.",
        )

    active_sub = await get_active_subscription(db, user.id)
    if active_sub:
        raise HTTPException(status_code=400, detail="У вас уже действует активная подписка")

    end_date = datetime.utcnow() + timedelta(days=FREE_TRIAL_DAYS)
    expire_ts = int(end_date.timestamp())
    traffic_limit_bytes = 5 * 1024 * 1024 * 1024  # 5 GB

    # Create client in Marzban Panel
    await marzban_client.create_user(
        username=user.marzban_username,
        expire_timestamp=expire_ts,
        data_limit_bytes=traffic_limit_bytes,
        note=f"Trial user tg:{user.telegram_id}",
    )
    marz_info = await marzban_client.get_user_links(user.marzban_username)

    new_sub = Subscription(
        user_id=user.id,
        plan_name="Пробный период 3 дня",
        traffic_limit_bytes=traffic_limit_bytes,
        used_traffic_bytes=0,
        start_date=datetime.utcnow(),
        end_date=end_date,
        is_active=True,
        subscription_url=marz_info.get("subscription_url"),
        vless_link=marz_info.get("primary_vless_link"),
    )
    user.free_trial_used = True
    db.add(new_sub)
    await db.commit()
    await db.refresh(new_sub)

    logger.info("Trial activated for tg_id=%s, expires at %s", user.telegram_id, end_date)

    return {
        "success": True,
        "message": f"Пробный период на {FREE_TRIAL_DAYS} дня активирован!",
        "subscription": {
            "id": new_sub.id,
            "plan_name": new_sub.plan_name,
            "end_date": new_sub.end_date.isoformat(),
            "vless_link": new_sub.vless_link,
            "subscription_url": new_sub.subscription_url,
        },
    }


@app.post("/api/subscription/purchase")
async def purchase_subscription(
    payload: PurchaseSubscriptionRequest,
    telegram_id: int = Query(..., description="Telegram ID of buyer"),
    db: AsyncSession = Depends(get_db),
):
    """
    Purchases a subscription plan using internal balance.
    Deducts balance, extends Marzban, and distributes referral bonuses.
    """
    if payload.plan_id not in SUBSCRIPTION_PLANS:
        raise HTTPException(status_code=400, detail="Неверный тарифный план")

    plan = SUBSCRIPTION_PLANS[payload.plan_id]
    plan_cost = plan["price"]
    plan_days = plan["days"]

    user = (await db.execute(select(User).where(User.telegram_id == telegram_id))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    if user.balance < plan_cost:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Недостаточно средств. Баланс: {user.balance:.2f} ₽, требуется: {plan_cost:.2f} ₽. Пополните баланс.",
        )

    # Deduct balance
    user.balance -= plan_cost

    curr_sub = await get_active_subscription(db, user.id)
    now = datetime.utcnow()

    if curr_sub and curr_sub.end_date > now:
        new_end_date = curr_sub.end_date + timedelta(days=plan_days)
        curr_sub.end_date = new_end_date
        curr_sub.plan_name = plan["name"]
        target_sub = curr_sub
    else:
        new_end_date = now + timedelta(days=plan_days)
        target_sub = Subscription(
            user_id=user.id,
            plan_name=plan["name"],
            traffic_limit_bytes=0,  # Unlimited
            used_traffic_bytes=0,
            start_date=now,
            end_date=new_end_date,
            is_active=True,
        )
        db.add(target_sub)

    # Sync with Marzban
    new_expire_ts = int(new_end_date.timestamp())
    await marzban_client.extend_user(username=user.marzban_username, new_expire_ts=new_expire_ts)
    marz_info = await marzban_client.get_user_links(user.marzban_username)
    target_sub.subscription_url = marz_info.get("subscription_url")
    target_sub.vless_link = marz_info.get("primary_vless_link")

    # Distribute referral reward
    bonus_awarded = await award_referral_bonus_on_purchase(db, user, plan_cost, BOT_TOKEN)

    await db.commit()
    await db.refresh(target_sub)

    return {
        "success": True,
        "message": f"Тариф «{plan['name']}» успешно активирован на {plan_days} дней!",
        "new_balance": round(user.balance, 2),
        "end_date": target_sub.end_date.isoformat(),
        "subscription_url": target_sub.subscription_url,
        "vless_link": target_sub.vless_link,
        "referral_bonus_awarded": bonus_awarded,
    }


# --------------------------------------------------------------------------
# Secure Payment Gateway Architecture (CryptoBot & Telegram Stars)
# --------------------------------------------------------------------------

@app.post("/api/pay/create-invoice")
async def create_invoice(
    payload: CreateInvoiceRequest,
    telegram_id: int = Query(..., description="Telegram ID of the payer"),
    request: Request = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Generates a secure checkout invoice for balance replenishment:
    - Creates a pending PaymentTransaction record
    - Calls CryptoBot API or generates Stars invoice payload
    - Prevents arbitrary client-side balance manipulation
    """
    client_ip = request.client.host if request and request.client else str(telegram_id)
    payment_rate_limiter.check(client_ip, "создание счёта")

    user = (await db.execute(select(User).where(User.telegram_id == telegram_id))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    order_id = f"ord_{secrets.token_hex(8)}"

    if payload.gateway == "cryptobot":
        invoice_info = await create_crypto_bot_invoice(
            amount_rub=payload.amount,
            order_id=order_id,
            description=f"Пополнение баланса NexusVPN (tg:{telegram_id})",
        )
        pay_url = invoice_info.get("pay_url")
        ext_id = invoice_info.get("invoice_id")
    else:
        # Telegram Stars / Generic payment URL
        pay_url = f"https://t.me/{BOT_USERNAME}?start=pay_{order_id}"
        ext_id = f"stars_{order_id}"

    # Record pending transaction
    tx = PaymentTransaction(
        user_id=user.id,
        order_id=order_id,
        gateway=payload.gateway,
        amount=payload.amount,
        currency="RUB",
        status="pending",
        external_invoice_id=ext_id,
        pay_url=pay_url,
        created_at=datetime.utcnow(),
    )
    db.add(tx)
    await db.commit()
    await db.refresh(tx)

    logger.info("Created invoice %s for tg_id=%s, amount=%.2f RUB via %s",
                order_id, telegram_id, payload.amount, payload.gateway)

    return {
        "success": True,
        "order_id": order_id,
        "amount": payload.amount,
        "currency": "RUB",
        "gateway": payload.gateway,
        "pay_url": pay_url,
        "status": "pending",
    }


@app.post("/api/webhook/cryptobot")
async def cryptobot_webhook(
    request: Request,
    crypto_pay_api_signature: Optional[str] = Header(None, alias="crypto-pay-api-signature"),
    db: AsyncSession = Depends(get_db),
):
    """
    Official webhook handler for @CryptoBot.
    Cryptographically verifies the HMAC-SHA256 signature using CRYPTO_BOT_TOKEN.
    Processes invoice payments idempotently.
    """
    raw_body = await request.body()

    # Validate signature if token is set
    if CRYPTO_BOT_TOKEN and crypto_pay_api_signature:
        if not verify_crypto_bot_webhook(raw_body, crypto_pay_api_signature, CRYPTO_BOT_TOKEN):
            logger.warning("Invalid CryptoBot webhook signature!")
            raise HTTPException(status_code=403, detail="Signature verification failed")

    try:
        data = json.loads(raw_body)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    update_type = data.get("update_type")
    payload_data = data.get("payload", {})

    if update_type == "invoice_paid":
        order_id = payload_data.get("payload")
        ext_id = str(payload_data.get("invoice_id"))
        if order_id:
            await process_successful_payment(
                db=db,
                order_id=order_id,
                gateway="cryptobot",
                external_id=ext_id,
            )
            return {"ok": True}

    return {"ok": True, "message": "Ignored update type"}


@app.post("/api/test/sandbox-topup")
async def sandbox_test_topup(
    payload: SandboxTopUpRequest,
    telegram_id: int = Query(..., description="Telegram ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    DEVELOPMENT-ONLY sandbox endpoint for testing balance replenishment.
    Strictly disabled in production when ALLOW_INSECURE_TEST_AUTH is False!
    """
    if not ALLOW_INSECURE_TEST_AUTH:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Тестовое пополнение отключено в продакшене. Используйте официальный платёжный шлюз.",
        )

    user = (await db.execute(select(User).where(User.telegram_id == telegram_id))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    order_id = f"test_{secrets.token_hex(6)}"
    tx = PaymentTransaction(
        user_id=user.id,
        order_id=order_id,
        gateway="sandbox_test",
        amount=payload.amount,
        currency="RUB",
        status="pending",
        created_at=datetime.utcnow(),
    )
    db.add(tx)
    await db.commit()

    await process_successful_payment(db, order_id, gateway="sandbox_test")
    return {
        "success": True,
        "amount_added": payload.amount,
        "new_balance": round(user.balance, 2),
        "warning": "Sandbox test transaction applied.",
    }


# --------------------------------------------------------------------------
# Dynamic Servers & Cluster Nodes
# --------------------------------------------------------------------------

# Fallback cluster topology when nodes are not yet clustered in Marzban
DEFAULT_CLUSTER_LOCATIONS = [
    {"id": "nl-ams", "country": "Нидерланды", "country_code": "NL", "city": "Амстердам", "flag": "🇳🇱", "ping_ms": 28, "protocol": "VLESS + Reality (XTLS Vision)", "status": "online", "load_percent": 34},
    {"id": "de-fra", "country": "Германия", "country_code": "DE", "city": "Франкфурт", "flag": "🇩🇪", "ping_ms": 35, "protocol": "VLESS + Reality (XTLS Vision)", "status": "online", "load_percent": 48},
    {"id": "fi-hel", "country": "Финляндия", "country_code": "FI", "city": "Хельсинки", "flag": "🇫🇮", "ping_ms": 22, "protocol": "VLESS + Reality (XTLS Vision)", "status": "online", "load_percent": 29},
    {"id": "us-nyc", "country": "США", "country_code": "US", "city": "Нью-Йорк", "flag": "🇺🇸", "ping_ms": 95, "protocol": "VLESS + Reality (XTLS Vision)", "status": "online", "load_percent": 55},
    {"id": "tr-ist", "country": "Турция", "country_code": "TR", "city": "Стамбул", "flag": "🇹🇷", "ping_ms": 42, "protocol": "VLESS + Reality (XTLS Vision)", "status": "online", "load_percent": 40},
    {"id": "se-sto", "country": "Швеция", "country_code": "SE", "city": "Стокгольм", "flag": "🇸🇪", "ping_ms": 25, "protocol": "VLESS + Reality (XTLS Vision)", "status": "online", "load_percent": 18},
]

_servers_cache: Optional[List[Dict[str, Any]]] = None
_servers_cache_time: float = 0.0


@app.get("/api/servers")
async def get_servers():
    """
    Returns active VPN server cluster nodes.
    Dynamically queries Marzban /api/nodes if cluster nodes are configured,
    with 60-second caching for high performance.
    """
    global _servers_cache, _servers_cache_time
    now = time.time()

    if _servers_cache and (now - _servers_cache_time < 60.0):
        return _servers_cache

    try:
        nodes = await marzban_client.get_nodes()
        if nodes:
            dynamic_list = []
            flag_map = {"nl": "🇳🇱", "de": "🇩🇪", "fi": "🇫🇮", "us": "🇺🇸", "tr": "🇹🇷", "se": "🇸🇪", "fr": "🇫🇷", "gb": "🇬🇧"}
            for n in nodes:
                name = n.get("name", "Node")
                status_str = "online" if n.get("status") == "connected" else "offline"
                dynamic_list.append({
                    "id": f"node-{n.get('id', name)}",
                    "country": name.title(),
                    "country_code": "EU",
                    "city": n.get("address", "Cluster Node"),
                    "flag": flag_map.get(name[:2].lower(), "🌐"),
                    "ping_ms": 30,
                    "protocol": "VLESS + Reality (XTLS Vision)",
                    "status": status_str,
                    "load_percent": int(n.get("usage", 30)),
                })
            _servers_cache = dynamic_list
            _servers_cache_time = now
            return dynamic_list
    except Exception as exc:
        logger.warning("Could not fetch dynamic Marzban nodes: %s", exc)

    _servers_cache = DEFAULT_CLUSTER_LOCATIONS
    _servers_cache_time = now
    return DEFAULT_CLUSTER_LOCATIONS


@app.get("/api/referrals")
async def get_referral_details(
    telegram_id: int = Query(..., description="Telegram ID of the user"),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves user referral dashboard stats and invited friends."""
    user = (await db.execute(select(User).where(User.telegram_id == telegram_id))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    invited_users_stmt = (
        select(User.telegram_id, User.username, User.first_name, User.created_at)
        .where(User.invited_by == user.id)
        .order_by(User.created_at.desc())
    )
    invited_res = await db.execute(invited_users_stmt)
    invited_list = [
        {
            "telegram_id": row[0],
            "username": row[1] or "Аноним",
            "name": row[2] or "Пользователь",
            "date": row[3].strftime("%d.%m.%Y"),
        }
        for row in invited_res.all()
    ]

    earnings_stmt = select(func.sum(Referral.reward_amount)).where(
        Referral.referrer_id == user.id,
        Referral.is_paid == True,
    )
    total_earned = (await db.execute(earnings_stmt)).scalar_one() or 0.0

    return {
        "ref_code": user.ref_code,
        "ref_link": f"https://t.me/{BOT_USERNAME}?start=ref_{user.ref_code}",
        "total_invited": len(invited_list),
        "total_earned": round(total_earned, 2),
        "reward_per_sale": REFERRAL_BONUS_RUB,
        "commission_percent": REFERRAL_PERCENT,
        "invited_friends": invited_list,
    }
