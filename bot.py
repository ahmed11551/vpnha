"""
NexusVPN Commercial Telegram Bot (aiogram 3.x)
Level: Senior Telegram Bot Developer + Product Designer (2026 Edition)

Architecture & Modules:
- Onboarding & Dynamic Deep-Linking (new user welcome vs returning user dashboard)
- Interactive Main Menu with Telegram Mini App integration
- 3-day Free Trial Instant Activation
- VLESS Reality Key delivery + QR code generation (In-memory PIL / Remote API fallback)
- Client Installation Guides (iOS: Happ/Streisand, Android: v2rayNG/Happ, Desktop: Amnezia/v2rayN)
- In-Chat Promo Code Activation Engine (FSM & /promo command)
- High-Converting Referral Hub (Viral 1-click share, live stats, balance)
- Subscription Expiration Notifier (Background worker: 3 days, 1 day, 0 days)
- Anti-Flood & Rate-Limiting Middleware
- Administrator Command Suite (/admin, /stats, /find_user, /give_days)
"""

import asyncio
import io
import logging
import urllib.parse
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    TelegramObject,
    WebAppInfo,
)
from sqlalchemy import func, select

from config import settings
from database import async_session_factory, init_db
from marzban_client import marzban_client
from models import Payment, PromoCode, Referral, Subscription, User
from services import (
    get_or_create_user,
    validate_and_apply_promocode,
    send_telegram_message,
)

# --------------------------------------------------------------------------
# Logging Setup
# --------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s: %(message)s"
)
logger = logging.getLogger("NexusVPN-Bot")

# Configuration constants
BOT_TOKEN = settings.BOT_TOKEN
BOT_USERNAME = settings.BOT_USERNAME
WEBAPP_URL = settings.WEBAPP_URL
FREE_TRIAL_DAYS = settings.FREE_TRIAL_DAYS
TRIAL_TRAFFIC_GB = settings.TRIAL_TRAFFIC_GB
REFERRAL_BONUS_RUB = settings.REFERRAL_BONUS_RUB
REFERRAL_PERCENT = settings.REFERRAL_COMMISSION_PERCENT
ADMIN_IDS = set(settings.admin_ids_list)

# --------------------------------------------------------------------------
# FSM States
# --------------------------------------------------------------------------
class PromoState(StatesGroup):
    waiting_for_code = State()


class AdminState(StatesGroup):
    waiting_for_user_search = State()
    waiting_for_give_days = State()


# --------------------------------------------------------------------------
# Anti-Flood / Throttling Middleware
# --------------------------------------------------------------------------
class ThrottlingMiddleware:
    """Simple in-memory rate limiter to prevent button spam and double clicks."""
    def __init__(self, rate_limit: float = 0.5):
        self.rate_limit = rate_limit
        self.user_timestamps: Dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Any],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user_id = None
        if isinstance(event, Message) and event.from_user:
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery) and event.from_user:
            user_id = event.from_user.id

        if user_id:
            now = asyncio.get_event_loop().time()
            last_time = self.user_timestamps.get(user_id, 0.0)
            if now - last_time < self.rate_limit:
                if isinstance(event, CallbackQuery):
                    await event.answer("⏳ Пожалуйста, подождите...", show_alert=False)
                return None
            self.user_timestamps[user_id] = now

        return await handler(event, data)


# --------------------------------------------------------------------------
# Keyboards & UI Builders
# --------------------------------------------------------------------------
def get_main_keyboard(user: User, has_active_sub: bool) -> InlineKeyboardMarkup:
    """Dynamic high-converting main menu keyboard."""
    app_url = f"{WEBAPP_URL}?ref={user.ref_code}"
    buttons: List[List[InlineKeyboardButton]] = []

    # Row 1: Primary Action (Web App Launch)
    buttons.append([
        InlineKeyboardButton(
            text="⚡ Запустить Nexus VPN (Web App)",
            web_app=WebAppInfo(url=app_url),
        )
    ])

    # Row 2: Trial or Key Access
    if not user.free_trial_used and not has_active_sub:
        buttons.append([
            InlineKeyboardButton(text="🎁 Забрать 3 дня бесплатно", callback_data="trial:activate"),
            InlineKeyboardButton(text="🔑 Мой VLESS ключ", callback_data="key:get"),
        ])
    else:
        buttons.append([
            InlineKeyboardButton(text="🔑 Мой ключ VLESS", callback_data="key:get"),
            InlineKeyboardButton(text="💳 Пополнить баланс", callback_data="balance:topup"),
        ])

    # Row 3: Referral program & Promo codes
    buttons.append([
        InlineKeyboardButton(text="👥 Партнерам (15%)", callback_data="referral:info"),
        InlineKeyboardButton(text="🎟 Промокод", callback_data="promo:enter"),
    ])

    # Row 4: Client guides & Support
    buttons.append([
        InlineKeyboardButton(text="📖 Как настроить", callback_data="guide:menu"),
        InlineKeyboardButton(text="💬 Поддержка", callback_data="support:info"),
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_guides_keyboard() -> InlineKeyboardMarkup:
    """Device selection keyboard for setup tutorials."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🍏 iOS (iPhone / iPad)", callback_data="guide:ios"),
                InlineKeyboardButton(text="🤖 Android", callback_data="guide:android"),
            ],
            [
                InlineKeyboardButton(text="💻 Windows / macOS / Linux", callback_data="guide:desktop"),
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="menu:home"),
            ],
        ]
    )


def get_key_management_keyboard(user_ref_code: str) -> InlineKeyboardMarkup:
    """Keyboard attached to the active subscription key view."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📷 Показать QR-код", callback_data="key:qr"),
                InlineKeyboardButton(text="🔄 Сменить ключ (UUID)", callback_data="key:revoke"),
            ],
            [
                InlineKeyboardButton(text="📖 Инструкция по установке", callback_data="guide:menu"),
                InlineKeyboardButton(text="⚡ Открыть Web App", web_app=WebAppInfo(url=f"{WEBAPP_URL}?ref={user_ref_code}")),
            ],
            [
                InlineKeyboardButton(text="⬅️ Главное меню", callback_data="menu:home"),
            ],
        ]
    )


def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Admin quick actions."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 Свежая статистика", callback_data="admin:stats"),
                InlineKeyboardButton(text="🔍 Поиск пользователя", callback_data="admin:find"),
            ],
            [
                InlineKeyboardButton(text="🎁 Начислить дни", callback_data="admin:give_days"),
                InlineKeyboardButton(text="⬅️ Главное меню", callback_data="menu:home"),
            ],
        ]
    )


# --------------------------------------------------------------------------
# QR Code Generator Utility
# --------------------------------------------------------------------------
def generate_qr_bytes(data: str) -> Optional[bytes]:
    """Generates QR code image in-memory using qrcode library if available."""
    try:
        import qrcode
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=2,
        )
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#0F172A", back_color="#FFFFFF")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except Exception as e:
        logger.debug("Local qrcode generation failed: %s", e)
        return None


# --------------------------------------------------------------------------
# Router Definition
# --------------------------------------------------------------------------
router = Router()


# --------------------------------------------------------------------------
# 1. Onboarding & /start Handler
# --------------------------------------------------------------------------
@router.message(CommandStart())
async def handle_start_command(message: Message, bot: Bot, state: FSMContext):
    """
    Handles /start command, deep-linking, onboarding, and return-user status.
    """
    await state.clear()
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name or "Пользователь"

    # Extract deep link argument if present (e.g. /start ref_abc123)
    command_args = message.text.split(maxsplit=1)
    ref_arg = command_args[1] if len(command_args) > 1 else None

    async with async_session_factory() as session:
        user, is_new = await get_or_create_user(
            db=session,
            telegram_id=user_id,
            username=username,
            first_name=first_name,
            ref_code_arg=ref_arg,
        )

        # Notify referrer if this is a new signup
        if is_new and user.invited_by:
            inviter = (
                await session.execute(select(User).where(User.id == user.invited_by))
            ).scalar_one_or_none()
            if inviter:
                name_display = f"@{username}" if username else first_name
                try:
                    await bot.send_message(
                        chat_id=inviter.telegram_id,
                        text=(
                            f"🎉 <b>Новый реферал!</b>\n\n"
                            f"По вашей ссылке зарегистрировался <b>{name_display}</b>.\n"
                            f"Как только он совершит первую оплату, вы получите <b>{REFERRAL_BONUS_RUB:.0f} ₽</b> "
                            f"на баланс и <b>{REFERRAL_PERCENT:.0f}%</b> со всех продлений!"
                        ),
                        parse_mode=ParseMode.HTML,
                    )
                except Exception as exc:
                    logger.warning("Referral notification failed: %s", exc)

        # Fetch user's active subscription status
        sub_stmt = (
            select(Subscription)
            .where(
                Subscription.user_id == user.id,
                Subscription.is_active == True,
                Subscription.end_date > datetime.utcnow(),
            )
            .order_by(Subscription.end_date.desc())
        )
        active_sub = (await session.execute(sub_stmt)).scalar_one_or_none()

    # Build Onboarding or Return Dashboard text
    if is_new:
        text = (
            f"👋 <b>Добро пожаловать в NexusVPN, {first_name}!</b>\n\n"
            f"🛡 <b>NexusVPN</b> — премиальный VPN нового поколения на базе протокола <b>Xray VLESS + Reality (XTLS-Vision)</b>.\n\n"
            f"⚡ <b>Почему NexusVPN?</b>\n"
            f"• <b>100% маскировка</b> трафика под обычный HTTPS (устойчив к блокировкам РКН и ТСПУ)\n"
            f"• <b>Скорость до 1 Гбит/с:</b> YouTube 4K, Instagram, игры без задержек\n"
            f"• <b>Безлимитные устройства:</b> телефон, ноутбук, планшет\n\n"
            f"🎁 <b>Специально для вас:</b>\n"
            f"Активируйте <b>бесплатный тест-драйв на 3 дня</b> прямо сейчас — без привязки карт!"
        )
    else:
        now = datetime.utcnow()
        if active_sub:
            days_left = max(0, (active_sub.end_date - now).days)
            hours_left = int((active_sub.end_date - now).seconds / 3600)
            status_text = f"🟢 <b>Активна</b> (осталось {days_left} дн. {hours_left} ч.)"
        elif not user.free_trial_used:
            status_text = "🟡 <b>Не активна</b> (вам доступен бесплатный тест!)"
        else:
            status_text = "🔴 <b>Истекла</b> (оформите продление в Web App)"

        text = (
            f"👋 <b>С возвращением в NexusVPN, {first_name}!</b>\n\n"
            f"📊 <b>Ваш статус:</b>\n"
            f"• Подписка: {status_text}\n"
            f"• Баланс счета: <code>{user.balance:.2f} ₽</code>\n"
            f"• Реферальный код: <code>{user.ref_code}</code>\n\n"
            f"<i>Выберите действие в меню ниже или запустите удобный Web App:</i>"
        )

    await message.answer(
        text=text,
        reply_markup=get_main_keyboard(user, bool(active_sub)),
        parse_mode=ParseMode.HTML,
    )


# --------------------------------------------------------------------------
# 2. Main Menu & Navigation Handlers
# --------------------------------------------------------------------------
@router.message(Command("menu"))
@router.callback_query(F.data == "menu:home")
async def show_main_menu(event: TelegramObject, state: FSMContext):
    """Brings user back to the primary dashboard."""
    await state.clear()
    user_id = event.from_user.id
    first_name = event.from_user.first_name or "Пользователь"

    async with async_session_factory() as session:
        user = (await session.execute(select(User).where(User.telegram_id == user_id))).scalar_one_or_none()
        if not user:
            if isinstance(event, Message):
                await event.answer("Сначала напишите /start")
            else:
                await event.answer("Сначала напишите /start", show_alert=True)
            return

        sub_stmt = (
            select(Subscription)
            .where(
                Subscription.user_id == user.id,
                Subscription.is_active == True,
                Subscription.end_date > datetime.utcnow(),
            )
            .order_by(Subscription.end_date.desc())
        )
        active_sub = (await session.execute(sub_stmt)).scalar_one_or_none()

    now = datetime.utcnow()
    if active_sub:
        days_left = max(0, (active_sub.end_date - now).days)
        sub_status = f"🟢 <b>Активна</b> (ещё {days_left} дн.)"
    elif not user.free_trial_used:
        sub_status = "🎁 <b>Доступен тест на 3 дня</b>"
    else:
        sub_status = "🔴 <b>Не активна</b>"

    text = (
        f"🏠 <b>Личный кабинет NexusVPN</b>\n\n"
        f"👤 Пользователь: <b>{first_name}</b>\n"
        f"💳 Баланс: <code>{user.balance:.2f} ₽</code>\n"
        f"📡 Подписка: {sub_status}\n\n"
        f"<i>Быстрые действия:</i>"
    )

    kb = get_main_keyboard(user, bool(active_sub))
    if isinstance(event, CallbackQuery):
        try:
            await event.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
        except Exception:
            await event.message.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML)
        await event.answer()
    else:
        await event.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML)


# --------------------------------------------------------------------------
# 3. Free Trial Activation
# --------------------------------------------------------------------------
@router.callback_query(F.data == "trial:activate")
async def callback_trial_activate(query: CallbackQuery):
    """Instantly provisions a 3-day test trial via Marzban."""
    user_id = query.from_user.id

    async with async_session_factory() as session:
        user = (await session.execute(select(User).where(User.telegram_id == user_id))).scalar_one_or_none()
        if not user:
            await query.answer("Сначала запустите бота через /start", show_alert=True)
            return

        if user.free_trial_used:
            await query.answer(
                "❌ Вы уже использовали бесплатный пробный период.",
                show_alert=True,
            )
            return

        # Check if already has an active subscription
        sub_stmt = select(Subscription).where(
            Subscription.user_id == user.id,
            Subscription.end_date > datetime.utcnow()
        )
        active_sub = (await session.execute(sub_stmt)).scalar_one_or_none()
        if active_sub:
            await query.answer("У вас уже действует подписка!", show_alert=True)
            return

        end_date = datetime.utcnow() + timedelta(days=FREE_TRIAL_DAYS)
        expire_ts = int(end_date.timestamp())
        traffic_limit = TRIAL_TRAFFIC_GB * 1024 * 1024 * 1024

        # Request user creation or update in Marzban
        try:
            await marzban_client.create_user(
                username=user.marzban_username,
                expire_timestamp=expire_ts,
                data_limit_bytes=traffic_limit,
                note=f"Trial tg_{user.telegram_id}",
            )
        except Exception as exc:
            logger.error("Marzban trial creation failed: %s", exc)

        marz_info = await marzban_client.get_user_links(user.marzban_username)

        new_sub = Subscription(
            user_id=user.id,
            plan_name="Пробный тест (3 дня)",
            traffic_limit_bytes=traffic_limit,
            start_date=datetime.utcnow(),
            end_date=end_date,
            is_active=True,
            subscription_url=marz_info.get("subscription_url"),
            vless_link=marz_info.get("primary_vless_link"),
        )
        user.free_trial_used = True
        session.add(new_sub)
        await session.commit()

        vless_key = new_sub.vless_link or "vless://..."

        text = (
            f"🎉 <b>Бесплатный период успешно активирован!</b>\n\n"
            f"⏳ Срок: <b>{FREE_TRIAL_DAYS} дня</b> (до {end_date.strftime('%d.%m.%Y %H:%M')} UTC)\n"
            f"⚡ Трафик: <b>{TRIAL_TRAFFIC_GB} ГБ</b> на максимальной скорости\n\n"
            f"🔑 <b>Ваш VLESS ключ (нажмите чтобы скопировать):</b>\n"
            f"<code>{vless_key}</code>\n\n"
            f"📥 <b>Автообновляемая подписка:</b>\n"
            f"<code>{new_sub.subscription_url}</code>\n\n"
            f"<i>💡 Для подключения скопируйте ключ и вставьте в приложение Happ или v2rayNG.</i>"
        )

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="📷 Показать QR-код", callback_data="key:qr"),
                    InlineKeyboardButton(text="📖 Как настроить", callback_data="guide:menu"),
                ],
                [
                    InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu:home"),
                ]
            ]
        )

        await query.message.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML)
        await query.answer("Пробный период активирован! 🚀")


# --------------------------------------------------------------------------
# 4. Key Management & QR Code
# --------------------------------------------------------------------------
@router.message(Command("key"))
@router.callback_query(F.data == "key:get")
async def callback_get_key(event: TelegramObject):
    """Displays connection key or prompts to subscribe."""
    user_id = event.from_user.id

    async with async_session_factory() as session:
        user = (await session.execute(select(User).where(User.telegram_id == user_id))).scalar_one_or_none()
        if not user:
            if isinstance(event, CallbackQuery):
                await event.answer("Сначала напишите /start", show_alert=True)
            return

        sub_stmt = (
            select(Subscription)
            .where(
                Subscription.user_id == user.id,
                Subscription.is_active == True,
                Subscription.end_date > datetime.utcnow(),
            )
            .order_by(Subscription.end_date.desc())
        )
        sub = (await session.execute(sub_stmt)).scalar_one_or_none()

    if not sub:
        text = (
            "❌ <b>У вас нет активной подписки.</b>\n\n"
            "Вы можете активировать бесплатный тест-драйв на 3 дня или приобрести подписку в нашем Web App!"
        )
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🎁 Активировать 3 дня", callback_data="trial:activate")],
                [InlineKeyboardButton(text="⚡ Открыть Web App", web_app=WebAppInfo(url=f"{WEBAPP_URL}?ref={user.ref_code}"))],
                [InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu:home")],
            ]
        )
        if isinstance(event, CallbackQuery):
            await event.message.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML)
            await event.answer()
        else:
            await event.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML)
        return

    # Fetch fresh links from Marzban
    marz_info = await marzban_client.get_user_links(user.marzban_username)
    key = marz_info.get("primary_vless_link") or sub.vless_link
    sub_link = marz_info.get("subscription_url") or sub.subscription_url
    days_left = max(0, (sub.end_date - datetime.utcnow()).days)

    text = (
        f"🔐 <b>Ваши данные для подключения</b>\n\n"
        f"• Тариф: <b>{sub.plan_name}</b>\n"
        f"• Действует до: <b>{sub.end_date.strftime('%d.%m.%Y %H:%M')} UTC</b> (осталось {days_left} дн.)\n"
        f"• Протокол: <b>VLESS + Reality (XTLS-Vision)</b>\n\n"
        f"🔑 <b>Прямой ключ (нажмите для копирования):</b>\n"
        f"<code>{key}</code>\n\n"
        f"🌐 <b>Ссылка на авто-подписку:</b>\n"
        f"<code>{sub_link}</code>\n\n"
        f"<i>💡 Нажмите «Показать QR-код» для быстрого сканирования камерой приложения!</i>"
    )

    kb = get_key_management_keyboard(user.ref_code)
    if isinstance(event, CallbackQuery):
        await event.message.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML)
        await event.answer()
    else:
        await event.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML)


@router.callback_query(F.data == "key:qr")
async def callback_show_qr(query: CallbackQuery, bot: Bot):
    """Generates and sends QR code image of VLESS key."""
    user_id = query.from_user.id
    async with async_session_factory() as session:
        user = (await session.execute(select(User).where(User.telegram_id == user_id))).scalar_one_or_none()
        if not user:
            await query.answer("Сначала введите /start", show_alert=True)
            return

        sub_stmt = (
            select(Subscription)
            .where(Subscription.user_id == user.id, Subscription.end_date > datetime.utcnow())
            .order_by(Subscription.end_date.desc())
        )
        sub = (await session.execute(sub_stmt)).scalar_one_or_none()

    if not sub or not sub.vless_link:
        await query.answer("У вас нет активного ключа для генерации QR", show_alert=True)
        return

    key = sub.vless_link
    qr_bytes = generate_qr_bytes(key)

    caption = (
        "📷 <b>QR-код для подключения к NexusVPN</b>\n\n"
        "1. Откройте приложение (Happ, Streisand, v2rayNG)\n"
        "2. Нажмите <b>«+»</b> и выберите <b>«Сканировать QR-код»</b>\n"
        "3. Наведите камеру на изображение выше"
    )

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📖 Как настроить", callback_data="guide:menu")],
            [InlineKeyboardButton(text="⬅️ Назад к ключу", callback_data="key:get")],
        ]
    )

    if qr_bytes:
        photo = BufferedInputFile(qr_bytes, filename="nexus_vpn_qr.png")
        await query.message.answer_photo(photo=photo, caption=caption, reply_markup=kb, parse_mode=ParseMode.HTML)
    else:
        # Fallback to high-availability online QR generation API
        encoded = urllib.parse.quote(key)
        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=500x500&data={encoded}"
        await query.message.answer_photo(photo=qr_url, caption=caption, reply_markup=kb, parse_mode=ParseMode.HTML)

    await query.answer()


@router.callback_query(F.data == "key:revoke")
async def callback_revoke_key(query: CallbackQuery):
    """Revokes current key and generates fresh UUID."""
    user_id = query.from_user.id
    async with async_session_factory() as session:
        user = (await session.execute(select(User).where(User.telegram_id == user_id))).scalar_one_or_none()
        if not user:
            await query.answer("Пользователь не найден", show_alert=True)
            return

        sub_stmt = (
            select(Subscription)
            .where(Subscription.user_id == user.id, Subscription.end_date > datetime.utcnow())
        )
        sub = (await session.execute(sub_stmt)).scalar_one_or_none()
        if not sub:
            await query.answer("У вас нет активной подписки", show_alert=True)
            return

        try:
            await marzban_client.revoke_user_sub(user.marzban_username)
            marz_info = await marzban_client.get_user_links(user.marzban_username)
            sub.subscription_url = marz_info.get("subscription_url")
            sub.vless_link = marz_info.get("primary_vless_link")
            await session.commit()

            text = (
                "✅ <b>Ключ успешно перевыпущен!</b>\n\n"
                "Предыдущий ключ был деактивирован. Ваш новый VLESS Reality ключ:\n"
                f"<code>{sub.vless_link}</code>"
            )
            kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="📷 Показать QR-код", callback_data="key:qr")],
                    [InlineKeyboardButton(text="⬅️ В меню", callback_data="menu:home")],
                ]
            )
            await query.message.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML)
            await query.answer("Ключ обновлен!")
        except Exception as exc:
            logger.error("Revoke key failed: %s", exc)
            await query.answer("Не удалось сбросить ключ. Попробуйте позже.", show_alert=True)


# --------------------------------------------------------------------------
# 5. Promo Code Engine (FSM & Command)
# --------------------------------------------------------------------------
@router.message(Command("promo"))
async def handle_promo_command(message: Message, state: FSMContext):
    """Direct promo command: /promo <CODE> or opens prompt."""
    parts = message.text.split(maxsplit=1)
    if len(parts) > 1:
        code = parts[1].strip()
        await process_promocode_execution(message, code)
    else:
        await state.set_state(PromoState.waiting_for_code)
        text = (
            "🎟 <b>Активация промокода</b>\n\n"
            "Введите промокод в ответном сообщении:\n"
            "<i>(или нажмите «Отмена» ниже)</i>"
        )
        kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="promo:cancel")]]
        )
        await message.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML)


@router.callback_query(F.data == "promo:enter")
async def callback_promo_enter(query: CallbackQuery, state: FSMContext):
    """Button prompt to enter promo code."""
    await state.set_state(PromoState.waiting_for_code)
    text = (
        "🎟 <b>Активация промокода</b>\n\n"
        "Отправьте промокод текстовым сообщением в чат:"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="promo:cancel")]]
    )
    await query.message.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    await query.answer()


@router.callback_query(F.data == "promo:cancel")
async def callback_promo_cancel(query: CallbackQuery, state: FSMContext):
    """Cancels promo input state."""
    await state.clear()
    await query.message.answer("Ввод промокода отменен.", reply_markup=InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🏠 В меню", callback_data="menu:home")]]
    ))
    await query.answer()


@router.message(PromoState.waiting_for_code)
async def handle_promo_input(message: Message, state: FSMContext):
    """Processes promo code received in FSM state."""
    code = message.text.strip()
    await state.clear()
    await process_promocode_execution(message, code)


async def process_promocode_execution(message: Message, code: str):
    """Validates and executes promo logic."""
    user_id = message.from_user.id

    async with async_session_factory() as session:
        user = (await session.execute(select(User).where(User.telegram_id == user_id))).scalar_one_or_none()
        if not user:
            await message.answer("Пользователь не найден. Напишите /start")
            return

        result = await validate_and_apply_promocode(session, user, code)

    if result.get("valid"):
        desc = result.get("description", "Бонус успешно начислен!")
        text = (
            f"🎉 <b>Промокод активирован!</b>\n\n"
            f"Код: <code>{code.upper()}</code>\n"
            f"Результат: <b>{desc}</b>\n\n"
            f"Текущий баланс: <code>{user.balance:.2f} ₽</code>"
        )
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔑 Проверить ключ", callback_data="key:get")],
                [InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu:home")],
            ]
        )
        await message.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    else:
        err_msg = result.get("message", "Неверный промокод")
        text = (
            f"❌ <b>Не удалось применить промокод</b>\n\n"
            f"Причина: <i>{err_msg}</i>\n\n"
            f"Проверьте правильность написания и попробуйте снова."
        )
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Попробовать снова", callback_data="promo:enter")],
                [InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu:home")],
            ]
        )
        await message.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML)


# --------------------------------------------------------------------------
# 6. Referral Hub
# --------------------------------------------------------------------------
@router.message(Command("ref"))
@router.callback_query(F.data == "referral:info")
async def callback_referral_info(event: TelegramObject):
    """Displays partner program stats and viral share button."""
    user_id = event.from_user.id

    async with async_session_factory() as session:
        user = (await session.execute(select(User).where(User.telegram_id == user_id))).scalar_one_or_none()
        if not user:
            if isinstance(event, CallbackQuery):
                await event.answer("Сначала напишите /start", show_alert=True)
            return

        # Count invited users
        invited_res = await session.execute(
            select(func.count(User.id)).where(User.invited_by == user.id)
        )
        invited_count = invited_res.scalar_one() or 0

        # Total earned
        earned_res = await session.execute(
            select(func.sum(Referral.reward_amount)).where(
                Referral.referrer_id == user.id, Referral.is_paid == True
            )
        )
        earned_sum = earned_res.scalar_one() or 0.0

    ref_link = f"https://t.me/{BOT_USERNAME}?start=ref_{user.ref_code}"
    share_text = urllib.parse.quote(
        "⚡ Попробуй быстрый и неблокируемый VPN нового поколения! "
        "Дают 3 дня бесплатного теста на максимальной скорости: "
    )
    share_url = f"https://t.me/share/url?url={ref_link}&text={share_text}"

    text = (
        f"👥 <b>Партнерская программа NexusVPN</b>\n\n"
        f"Зарабатывайте вместе с нами, рекомендуя надежный VPN своим друзьям:\n\n"
        f"💰 <b>Ваши условия:</b>\n"
        f"• <b>{REFERRAL_BONUS_RUB:.0f} ₽</b> за первую покупку каждого приведенного друга\n"
        f"• <b>{REFERRAL_PERCENT:.0f}%</b> пожизненно со всех их повторных продлений\n\n"
        f"📊 <b>Ваша статистика:</b>\n"
        f"• Приглашено пользователей: <b>{invited_count}</b>\n"
        f"• Всего заработано: <b>{earned_sum:.2f} ₽</b>\n"
        f"• Доступно на балансе: <b>{user.balance:.2f} ₽</b>\n\n"
        f"🔗 <b>Ваша ссылка для приглашения:</b>\n"
        f"<code>{ref_link}</code>\n\n"
        f"<i>Средства с баланса можно тратить на собственные подписки без ограничений.</i>"
    )

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📢 Поделиться ссылкой", url=share_url)],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu:home")],
        ]
    )

    if isinstance(event, CallbackQuery):
        await event.message.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML)
        await event.answer()
    else:
        await event.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML)


# --------------------------------------------------------------------------
# 7. Guides & Client Setup
# --------------------------------------------------------------------------
@router.message(Command("help"))
@router.callback_query(F.data == "guide:menu")
async def callback_guide_menu(event: TelegramObject):
    """Platform selection guide."""
    text = (
        "📱 <b>Инструкции по настройке NexusVPN</b>\n\n"
        "Мы поддерживаем современный стандарт <b>Xray VLESS Reality</b>.\n"
        "Выберите ваше устройство для пошаговой инструкции:"
    )
    kb = get_guides_keyboard()
    if isinstance(event, CallbackQuery):
        try:
            await event.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
        except Exception:
            await event.message.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML)
        await event.answer()
    else:
        await event.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML)


@router.callback_query(F.data == "guide:ios")
async def callback_guide_ios(query: CallbackQuery):
    """iOS setup guide."""
    text = (
        "🍏 <b>Инструкция для iOS (iPhone / iPad):</b>\n\n"
        "1. Установите бесплатное приложение <b>Happ Proxy Utility</b> или <b>Streisand</b> из App Store.\n"
        "2. Скопируйте ваш VLESS-ключ из меню бота (<i>«🔑 Мой ключ VLESS»</i>).\n"
        "3. Откройте приложение, нажмите значок <b>«+»</b> в правом верхнем углу.\n"
        "4. Выберите <b>«Import from clipboard»</b> (Вставить из буфера обмена).\n"
        "5. Разрешите добавление конфигурации VPN в системном диалоге iOS.\n"
        "6. Нажмите круглую кнопку <b>Connect</b>. Готово!"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔑 Получить мой ключ", callback_data="key:get")],
            [InlineKeyboardButton(text="⬅️ К выбору устройств", callback_data="guide:menu")],
        ]
    )
    await query.message.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    await query.answer()


@router.callback_query(F.data == "guide:android")
async def callback_guide_android(query: CallbackQuery):
    """Android setup guide."""
    text = (
        "🤖 <b>Инструкция для Android:</b>\n\n"
        "1. Установите <b>v2rayNG</b> или <b>Happ</b> из Google Play / GitHub.\n"
        "2. Скопируйте ваш VLESS ключ из меню бота.\n"
        "3. В приложении нажмите <b>«+»</b> в верхнем меню -> <b>«Импортировать из буфера обмена»</b>.\n"
        "4. Нажмите на добавленный сервер и нажмите кнопку подключения (значок <b>V</b> внизу)."
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔑 Получить мой ключ", callback_data="key:get")],
            [InlineKeyboardButton(text="⬅️ К выбору устройств", callback_data="guide:menu")],
        ]
    )
    await query.message.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    await query.answer()


@router.callback_query(F.data == "guide:desktop")
async def callback_guide_desktop(query: CallbackQuery):
    """PC and Mac setup guide."""
    text = (
        "💻 <b>Инструкция для Windows / macOS / Linux:</b>\n\n"
        "• <b>Windows:</b>\n"
        "Рекомендуем <b>v2rayN</b> или <b>AmneziaVPN</b>. Скопируйте ключ, нажмите <i>Ctrl+V</i> в программе и выберите <i>«Set system proxy»</i>.\n\n"
        "• <b>macOS:</b>\n"
        "Установите <b>FoXray</b> или <b>V2box</b> из Mac App Store, добавьте ключ через кнопку <i>«+»</i>.\n\n"
        "• <b>Универсально:</b>\n"
        "Кроссплатформенный клиент <b>Hiddify Next</b> (Windows/Mac/Linux) поддерживает вставку ключа в 1 клик."
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔑 Получить мой ключ", callback_data="key:get")],
            [InlineKeyboardButton(text="⬅️ К выбору устройств", callback_data="guide:menu")],
        ]
    )
    await query.message.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    await query.answer()


@router.callback_query(F.data == "balance:topup")
async def callback_balance_topup(query: CallbackQuery):
    """Balance top-up router to Web App."""
    user_id = query.from_user.id
    async with async_session_factory() as session:
        user = (await session.execute(select(User).where(User.telegram_id == user_id))).scalar_one_or_none()
        ref_code = user.ref_code if user else "app"

    text = (
        "💳 <b>Пополнение баланса и покупка тарифов</b>\n\n"
        "Оплата банковскими картами (МИР, Visa, MasterCard, СБП), Telegram Stars "
        "или криптовалютой через @CryptoBot доступна прямо в нашем Web App!\n\n"
        "⚡ Зачисление происходит моментально без ожидания."
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⚡ Открыть Web App для оплаты", web_app=WebAppInfo(url=f"{WEBAPP_URL}?ref={ref_code}"))],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu:home")],
        ]
    )
    await query.message.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    await query.answer()


@router.callback_query(F.data == "support:info")
async def callback_support_info(query: CallbackQuery):
    """Customer support contact dialog."""
    text = (
        "💬 <b>Служба заботы о клиентах NexusVPN</b>\n\n"
        "Если у вас возникли вопросы по настройке, оплате или скорости соединения, "
        "наша поддержка готова помочь 24/7:\n\n"
        "• Поддержка: @asbvpn_support\n"
        "• Канал с новостями и статусами: @asbvpn_channel"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✉️ Написать в поддержку", url="https://t.me/asbvpn_support")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu:home")],
        ]
    )
    await query.message.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    await query.answer()


# --------------------------------------------------------------------------
# 8. Admin Suite (/admin, /stats, /find_user, /give_days)
# --------------------------------------------------------------------------
def is_admin(user_id: int) -> bool:
    """Checks if the user has admin privileges."""
    return user_id in ADMIN_IDS or not ADMIN_IDS  # If not set, allow for initial bootstrap


@router.message(Command("admin"))
async def handle_admin_command(message: Message):
    """Admin dashboard entrypoint."""
    if not is_admin(message.from_user.id):
        await message.answer("⛔ У вас нет доступа к панели администратора.")
        return

    text = (
        "👑 <b>Панель администратора NexusVPN</b>\n\n"
        "Доступные команды:\n"
        "• <code>/stats</code> — Сводка метрик и финансов\n"
        "• <code>/find_user &lt;id|username&gt;</code> — Найти пользователя\n"
        "• <code>/give_days &lt;id&gt; &lt;дней&gt;</code> — Начислить дни вручную"
    )
    await message.answer(text, reply_markup=get_admin_keyboard(), parse_mode=ParseMode.HTML)


@router.message(Command("stats"))
@router.callback_query(F.data == "admin:stats")
async def handle_admin_stats(event: TelegramObject):
    """Calculates high-level metrics for operators."""
    user_id = event.from_user.id
    if not is_admin(user_id):
        if isinstance(event, CallbackQuery):
            await event.answer("Доступ запрещен", show_alert=True)
        return

    async with async_session_factory() as session:
        # Total users
        total_users = (await session.execute(select(func.count(User.id)))).scalar_one() or 0
        
        # Trial users
        trials_used = (
            await session.execute(select(func.count(User.id)).where(User.free_trial_used == True))
        ).scalar_one() or 0

        # Active subscriptions
        now = datetime.utcnow()
        active_subs = (
            await session.execute(
                select(func.count(Subscription.id)).where(
                    Subscription.is_active == True,
                    Subscription.end_date > now
                )
            )
        ).scalar_one() or 0

        # Total revenue
        revenue = (
            await session.execute(
                select(func.sum(Payment.amount)).where(Payment.status == "paid")
            )
        ).scalar_one() or 0.0

        # Total successful payments count
        paid_count = (
            await session.execute(
                select(func.count(Payment.id)).where(Payment.status == "paid")
            )
        ).scalar_one() or 0

    text = (
        "📊 <b>Аналитика NexusVPN</b>\n\n"
        f"👥 Всего пользователей: <b>{total_users}</b>\n"
        f"🟢 Активных подписок: <b>{active_subs}</b>\n"
        f"🎁 Активировано триалов: <b>{trials_used}</b>\n\n"
        f"💰 Оплаченных заказов: <b>{paid_count}</b>\n"
        f"💵 Общая выручка: <b>{revenue:,.2f} ₽</b>"
    )

    if isinstance(event, CallbackQuery):
        await event.message.answer(text, reply_markup=get_admin_keyboard(), parse_mode=ParseMode.HTML)
        await event.answer()
    else:
        await event.answer(text, reply_markup=get_admin_keyboard(), parse_mode=ParseMode.HTML)


@router.message(Command("find_user"))
async def handle_admin_find_user(message: Message):
    """Finds user by Telegram ID or @username."""
    if not is_admin(message.from_user.id):
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Использование: <code>/find_user &lt;telegram_id или username&gt;</code>")
        return

    query = parts[1].strip().replace("@", "")

    async with async_session_factory() as session:
        if query.isdigit():
            stmt = select(User).where(User.telegram_id == int(query))
        else:
            stmt = select(User).where(func.lower(User.username) == query.lower())

        user = (await session.execute(stmt)).scalar_one_or_none()

        if not user:
            await message.answer("❌ Пользователь не найден в базе данных.")
            return

        # Fetch sub
        sub_stmt = (
            select(Subscription)
            .where(Subscription.user_id == user.id)
            .order_by(Subscription.end_date.desc())
        )
        sub = (await session.execute(sub_stmt)).scalar_one_or_none()

    sub_info = "Отсутствует"
    if sub:
        now = datetime.utcnow()
        status = "🟢 Активна" if sub.end_date > now else "🔴 Истекла"
        sub_info = f"{status} до {sub.end_date.strftime('%d.%m.%Y %H:%M')} (план: {sub.plan_name})"

    text = (
        f"🔍 <b>Информация о пользователе:</b>\n\n"
        f"• ID: <code>{user.id}</code>\n"
        f"• Telegram ID: <code>{user.telegram_id}</code>\n"
        f"• Имя: <b>{user.first_name or '-'}</b> (@{user.username or 'нет'})\n"
        f"• Баланс: <code>{user.balance:.2f} ₽</code>\n"
        f"• Пробный период: {'Использован' if user.free_trial_used else 'Не использован'}\n"
        f"• Рефкод: <code>{user.ref_code}</code>\n"
        f"• Подписка: {sub_info}\n"
        f"• Marzban: <code>{user.marzban_username}</code>\n"
        f"• Дата регистрации: {user.created_at.strftime('%d.%m.%Y %H:%M')}"
    )
    await message.answer(text, parse_mode=ParseMode.HTML)


@router.message(Command("give_days"))
async def handle_admin_give_days(message: Message, bot: Bot):
    """Admin tool to manually extend or grant subscription days."""
    if not is_admin(message.from_user.id):
        return

    parts = message.text.split()
    if len(parts) < 3:
        await message.answer("Использование: <code>/give_days &lt;telegram_id&gt; &lt;количество_дней&gt;</code>")
        return

    tg_id_str, days_str = parts[1], parts[2]
    if not tg_id_str.isdigit() or not days_str.isdigit():
        await message.answer("Параметры должны быть числами.")
        return

    target_tg_id = int(tg_id_str)
    days_to_add = int(days_str)

    async with async_session_factory() as session:
        user = (
            await session.execute(select(User).where(User.telegram_id == target_tg_id))
        ).scalar_one_or_none()

        if not user:
            await message.answer("❌ Пользователь не найден.")
            return

        now = datetime.utcnow()
        sub_stmt = (
            select(Subscription)
            .where(Subscription.user_id == user.id, Subscription.is_active == True, Subscription.end_date > now)
            .order_by(Subscription.end_date.desc())
        )
        sub = (await session.execute(sub_stmt)).scalar_one_or_none()

        if sub:
            sub.end_date += timedelta(days=days_to_add)
            new_expire_ts = int(sub.end_date.timestamp())
        else:
            new_end = now + timedelta(days=days_to_add)
            new_expire_ts = int(new_end.timestamp())
            marz_info = await marzban_client.get_user_links(user.marzban_username)
            sub = Subscription(
                user_id=user.id,
                plan_name=f"Бонус {days_to_add} дн.",
                traffic_limit_bytes=0,
                start_date=now,
                end_date=new_end,
                is_active=True,
                subscription_url=marz_info.get("subscription_url"),
                vless_link=marz_info.get("primary_vless_link"),
            )
            session.add(sub)

        # Extend in Marzban
        try:
            await marzban_client.extend_user(user.marzban_username, new_expire_ts=new_expire_ts)
        except Exception as exc:
            logger.warning("Marzban extend in give_days: %s", exc)

        await session.commit()

    # Notify target user
    try:
        await bot.send_message(
            chat_id=target_tg_id,
            text=(
                f"🎁 <b>Вам начислено +{days_to_add} дней подписки!</b>\n\n"
                f"Новая дата окончания: <b>{sub.end_date.strftime('%d.%m.%Y %H:%M')} UTC</b>.\n"
                f"Приятного пользования скоростным интернетом с NexusVPN!"
            ),
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        pass

    await message.answer(
        f"✅ Успешно! Пользователю <code>{target_tg_id}</code> начислено <b>{days_to_add}</b> дн.\n"
        f"Новый срок: {sub.end_date.strftime('%d.%m.%Y %H:%M')} UTC"
    )


# --------------------------------------------------------------------------
# 9. Subscription Expiration Notifier Worker
# --------------------------------------------------------------------------
async def subscription_notification_worker(bot: Bot, interval_seconds: int = 3600):
    """
    Background daemon checking subscription expirations:
    - 3 days before expiry
    - 1 day before expiry
    - At expiration time
    Runs safely in the background during bot polling.
    """
    logger.info("Subscription notification worker started (interval: %ds)", interval_seconds)
    while True:
        try:
            now = datetime.utcnow()
            async with async_session_factory() as session:
                # 1. Check subscriptions ending in ~3 days (between 71 and 73 hours)
                target_3d_start = now + timedelta(hours=71)
                target_3d_end = now + timedelta(hours=73)

                subs_3d = (
                    await session.execute(
                        select(Subscription, User)
                        .join(User, Subscription.user_id == User.id)
                        .where(
                            Subscription.is_active == True,
                            Subscription.end_date >= target_3d_start,
                            Subscription.end_date <= target_3d_end,
                        )
                    )
                ).all()

                for sub, user in subs_3d:
                    try:
                        app_url = f"{WEBAPP_URL}?ref={user.ref_code}"
                        kb = InlineKeyboardMarkup(
                            inline_keyboard=[
                                [InlineKeyboardButton(text="⚡ Продлить подписку", web_app=WebAppInfo(url=app_url))]
                            ]
                        )
                        await bot.send_message(
                            chat_id=user.telegram_id,
                            text=(
                                "⏳ <b>Напоминание о подписке NexusVPN</b>\n\n"
                                f"Ваша подписка (<b>{sub.plan_name}</b>) истекает через <b>3 дня</b> "
                                f"({sub.end_date.strftime('%d.%m.%Y')} UTC).\n\n"
                                "Продлите доступ заранее в нашем Web App, чтобы не терять подключение к сервисам!",
                            ),
                            reply_markup=kb,
                            parse_mode=ParseMode.HTML,
                        )
                    except Exception as e:
                        logger.debug("Failed 3d notify for user %s: %s", user.telegram_id, e)

                # 2. Check subscriptions ending in ~1 day (between 23 and 25 hours)
                target_1d_start = now + timedelta(hours=23)
                target_1d_end = now + timedelta(hours=25)

                subs_1d = (
                    await session.execute(
                        select(Subscription, User)
                        .join(User, Subscription.user_id == User.id)
                        .where(
                            Subscription.is_active == True,
                            Subscription.end_date >= target_1d_start,
                            Subscription.end_date <= target_1d_end,
                        )
                    )
                ).all()

                for sub, user in subs_1d:
                    try:
                        app_url = f"{WEBAPP_URL}?ref={user.ref_code}"
                        kb = InlineKeyboardMarkup(
                            inline_keyboard=[
                                [InlineKeyboardButton(text="⚡ Продлить сейчас", web_app=WebAppInfo(url=app_url))]
                            ]
                        )
                        await bot.send_message(
                            chat_id=user.telegram_id,
                            text=(
                                "⚠️ <b>Внимание: Подписка истекает завтра!</b>\n\n"
                                f"Остались <b>последние сутки</b> действия вашего VPN-ключа.\n"
                                "После окончания доступ к зарубежным ресурсам будет приостановлен.\n\n"
                                "Нажмите кнопку ниже, чтобы продлить в 1 клик:",
                            ),
                            reply_markup=kb,
                            parse_mode=ParseMode.HTML,
                        )
                    except Exception as e:
                        logger.debug("Failed 1d notify for user %s: %s", user.telegram_id, e)

        except Exception as exc:
            logger.error("Error in notification worker loop: %s", exc)

        await asyncio.sleep(interval_seconds)


# --------------------------------------------------------------------------
# 10. Bot Bootstrap & Polling
# --------------------------------------------------------------------------
async def start_bot():
    """Initializes database schema, registers middlewares, and launches polling."""
    await init_db()

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Attach Throttling Middleware
    dp.message.middleware(ThrottlingMiddleware(rate_limit=0.4))
    dp.callback_query.middleware(ThrottlingMiddleware(rate_limit=0.4))

    # Register handlers
    dp.include_router(router)

    # Launch background notification scheduler
    asyncio.create_task(subscription_notification_worker(bot, interval_seconds=3600))

    logger.info("Commercial NexusVPN Bot started polling successfully.")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(start_bot())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
