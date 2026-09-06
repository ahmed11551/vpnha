"""
Telegram Bot implementation on aiogram 3.x for NexusVPN.
Features:
- /start handler with referral deep links parsing (/start ref_code)
- Inline WebApp button launching the Telegram Mini App
- Instant 3-day Free Trial activation
- Direct VLESS+Reality key retrieval for Happ, Amnezia, v2rayNG, Shadowrocket
- Interactive referral dashboard & notifications
- Step-by-step client configuration guides
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Optional

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    WebAppInfo,
)
from sqlalchemy import func, select

from database import async_session_factory, init_db
from marzban_client import marzban_client
from models import Referral, Subscription, User, PaymentTransaction
from services import get_or_create_user, create_crypto_bot_invoice, send_telegram_message

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("NexusVPN-Bot")

# Environment configs
BOT_TOKEN = os.getenv("BOT_TOKEN", "123456789:ABCdefGHIjklMNOpqrSTUvwxYZ")
BOT_USERNAME = os.getenv("BOT_USERNAME", "NexusVpnBot")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://nexus-vpn.demo.app/mini-app")
FREE_TRIAL_DAYS = int(os.getenv("FREE_TRIAL_DAYS", "3"))
REFERRAL_BONUS_RUB = float(os.getenv("REFERRAL_BONUS_RUB", "100.0"))

router = Router()


# --------------------------------------------------------------------------
# Keyboards
# --------------------------------------------------------------------------

def get_main_keyboard(user_ref_code: str) -> InlineKeyboardMarkup:
    """Main menu inline keyboard with Mini App and direct quick actions."""
    # Ensure WebApp URL has referral parameter
    app_url = f"{WEBAPP_URL}?ref={user_ref_code}"
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⚡ Открыть Nexus VPN (Mini App)",
                    web_app=WebAppInfo(url=app_url),
                )
            ],
            [
                InlineKeyboardButton(text="🎁 3 Дня бесплатно", callback_data="trial:activate"),
                InlineKeyboardButton(text="🔑 Мой ключ VLESS", callback_data="key:get"),
            ],
            [
                InlineKeyboardButton(text="👥 Реферальная система", callback_data="referral:info"),
                InlineKeyboardButton(text="📖 Как настроить", callback_data="guide:menu"),
            ],
            [
                InlineKeyboardButton(text="💳 Пополнить баланс", callback_data="balance:topup"),
            ],
        ]
    )
    return keyboard


def get_guides_keyboard() -> InlineKeyboardMarkup:
    """Navigation for client setup guides."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🍏 iOS (Happ / Streisand)", callback_data="guide:ios"),
                InlineKeyboardButton(text="🤖 Android (v2rayNG / Happ)", callback_data="guide:android"),
            ],
            [
                InlineKeyboardButton(text="💻 Windows / macOS (Amnezia / v2rayN)", callback_data="guide:desktop"),
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="menu:back"),
            ],
        ]
    )
    return keyboard


# --------------------------------------------------------------------------
# Bot Message Handlers
# --------------------------------------------------------------------------

@router.message(CommandStart())
async def handle_start_command(message: Message, bot: Bot):
    """
    Handles /start and deep-linking arguments:
    e.g. /start ref_abc123
    """
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name

    # Extract deep link argument if present
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

        if is_new and user.invited_by:
            # Notify inviter
            inviter = (await session.execute(select(User).where(User.id == user.invited_by))).scalar_one_or_none()
            if inviter:
                name_display = f"@{username}" if username else (first_name or "Новый друг")
                try:
                    await bot.send_message(
                        chat_id=inviter.telegram_id,
                        text=(
                            f"🎉 <b>По вашей ссылке зарегистрировался:</b> {name_display}!\n"
                            f"При его первой оплате подписки вы получите бонус <b>{REFERRAL_BONUS_RUB:.0f} ₽</b>!"
                        ),
                        parse_mode=ParseMode.HTML,
                    )
                except Exception as e:
                    logger.warning("Could not send referral alert: %s", e)

    greeting_text = (
        f"👋 <b>Добро пожаловать в NexusVPN, {first_name}!</b>\n\n"
        f"🛡 <b>NexusVPN</b> — сверхскоростной приватный VPN нового поколения на базе <b>Xray VLESS + Reality</b>.\n"
        f"Полная маскировка под обычный HTTPS трафик (XTLS-Vision), устойчивость к любым блокировкам РКН и DPI.\n\n"
        f"📊 <b>Ваш статус:</b>\n"
        f"• Баланс: <code>{user.balance:.2f} ₽</code>\n"
        f"• Пробный период: <code>{'Использован' if user.free_trial_used else 'Доступен (3 дня)'}</code>\n"
        f"• Реферальный код: <code>{user.ref_code}</code>\n\n"
        f"<i>Нажмите кнопку ниже, чтобы открыть веб-приложение или забрать бесплатный доступ:</i>"
    )

    await message.answer(
        text=greeting_text,
        reply_markup=get_main_keyboard(user.ref_code),
        parse_mode=ParseMode.HTML,
    )


# --------------------------------------------------------------------------
# Callback Query Handlers
# --------------------------------------------------------------------------

@router.callback_query(F.data == "trial:activate")
async def callback_trial_activate(query: CallbackQuery):
    """Activates 3-day trial from inline button."""
    user_id = query.from_user.id

    async with async_session_factory() as session:
        stmt = select(User).where(User.telegram_id == user_id)
        res = await session.execute(stmt)
        user = res.scalar_one_or_none()

        if not user:
            await query.answer("Пользователь не найден. Введите /start", show_alert=True)
            return

        if user.free_trial_used:
            await query.answer(
                "❌ Пробный период уже был использован ранее.",
                show_alert=True,
            )
            return

        # Check existing active subscription
        sub_stmt = (
            select(Subscription)
            .where(Subscription.user_id == user.id, Subscription.end_date > datetime.utcnow())
        )
        active_sub = (await session.execute(sub_stmt)).scalar_one_or_none()
        if active_sub:
            await query.answer("У вас уже действует подписка!", show_alert=True)
            return

        end_date = datetime.utcnow() + timedelta(days=FREE_TRIAL_DAYS)
        expire_ts = int(end_date.timestamp())
        traffic_limit = 5 * 1024 * 1024 * 1024  # 5GB

        # Call Marzban API
        await marzban_client.create_user(
            username=user.marzban_username,
            expire_timestamp=expire_ts,
            data_limit_bytes=traffic_limit,
            note=f"Telegram trial {user.telegram_id}",
        )

        marz_info = await marzban_client.get_user_links(user.marzban_username)

        new_sub = Subscription(
            user_id=user.id,
            plan_name="Пробный период 3 дня",
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

        await query.message.answer(
            f"🎉 <b>Пробный период успешно активирован!</b>\n\n"
            f"⏳ Срок действия: <b>3 дня</b> (до {end_date.strftime('%d.%m.%Y %H:%M')} UTC)\n"
            f"⚡ Трафик: <b>5 ГБ</b> на максимальной скорости\n\n"
            f"🔑 <b>Ваш VLESS ключ (нажмите для копирования):</b>\n"
            f"<code>{vless_key}</code>\n\n"
            f"📥 <b>Ссылка на автообновляемую подписку:</b>\n"
            f"<code>{new_sub.subscription_url}</code>\n\n"
            f"Для подключения вставьте этот ключ в приложение <b>Happ</b> (iOS/Android), <b>AmneziaVPN</b> или <b>v2rayNG</b>.",
            parse_mode=ParseMode.HTML,
        )
        await query.answer("Пробный период активирован!")


@router.callback_query(F.data == "key:get")
async def callback_get_key(query: CallbackQuery):
    """Returns active VLESS Reality key or prompts to subscribe."""
    user_id = query.from_user.id

    async with async_session_factory() as session:
        stmt = select(User).where(User.telegram_id == user_id)
        user = (await session.execute(stmt)).scalar_one_or_none()

        if not user:
            await query.answer("Сначала напишите /start", show_alert=True)
            return

        sub_stmt = (
            select(Subscription)
            .where(Subscription.user_id == user.id, Subscription.end_date > datetime.utcnow())
            .order_by(Subscription.end_date.desc())
        )
        sub = (await session.execute(sub_stmt)).scalar_one_or_none()

        if not sub:
            await query.message.answer(
                "❌ <b>У вас нет активной подписки.</b>\n\n"
                "Вы можете активировать бесплатный тест на 3 дня или оформить подписку в Mini App!",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="🎁 Активировать 3 дня", callback_data="trial:activate")],
                        [InlineKeyboardButton(text="⚡ Открыть Mini App", web_app=WebAppInfo(url=f"{WEBAPP_URL}?ref={user.ref_code}"))],
                    ]
                ),
                parse_mode=ParseMode.HTML,
            )
            await query.answer()
            return

        # Fetch latest info from Marzban
        marz_info = await marzban_client.get_user_links(user.marzban_username)
        key = marz_info.get("primary_vless_link") or sub.vless_link
        sub_link = marz_info.get("subscription_url") or sub.subscription_url

        days_left = max(0, (sub.end_date - datetime.utcnow()).days)

        await query.message.answer(
            f"🔐 <b>Ваши данные для подключения к NexusVPN</b>\n\n"
            f"• Тариф: <b>{sub.plan_name}</b>\n"
            f"• Действует до: <b>{sub.end_date.strftime('%d.%m.%Y %H:%M')}</b> (осталось {days_left} дн.)\n"
            f"• Протокол: <b>VLESS + Reality (XTLS-Vision)</b>\n\n"
            f"🔑 <b>Прямой ключ (нажмите чтобы скопировать):</b>\n"
            f"<code>{key}</code>\n\n"
            f"🌐 <b>Подписка для автоматического обновления серверов:</b>\n"
            f"<code>{sub_link}</code>",
            parse_mode=ParseMode.HTML,
        )
        await query.answer()


@router.callback_query(F.data == "referral:info")
async def callback_referral_info(query: CallbackQuery):
    """Displays referral dashboard in bot."""
    user_id = query.from_user.id

    async with async_session_factory() as session:
        stmt = select(User).where(User.telegram_id == user_id)
        user = (await session.execute(stmt)).scalar_one_or_none()

        if not user:
            await query.answer("Сначала напишите /start", show_alert=True)
            return

        # Count invited
        invited_res = await session.execute(
            select(func.count(User.id)).where(User.invited_by == user.id)
        )
        invited_count = invited_res.scalar_one() or 0

        # Total bonus earned
        earned_res = await session.execute(
            select(func.sum(Referral.reward_amount)).where(
                Referral.referrer_id == user.id, Referral.is_paid == True
            )
        )
        earned_sum = earned_res.scalar_one() or 0.0

        ref_link = f"https://t.me/{BOT_USERNAME}?start=ref_{user.ref_code}"

        text = (
            f"👥 <b>Партнерская программа NexusVPN</b>\n\n"
            f"Приглашайте друзей и получайте <b>{REFERRAL_BONUS_RUB:.0f} ₽</b> за каждую первую покупку друга + <b>15%</b> с повторных продлений!\n\n"
            f"📊 <b>Ваша статистика:</b>\n"
            f"• Приглашено пользователей: <b>{invited_count}</b>\n"
            f"• Заработано всего: <b>{earned_sum:.2f} ₽</b>\n"
            f"• Доступный баланс: <b>{user.balance:.2f} ₽</b>\n\n"
            f"🔗 <b>Ваша реферальная ссылка:</b>\n"
            f"<code>{ref_link}</code>\n\n"
            f"<i>Деньги на балансе можно использовать для оплаты любых VPN-тарифов!</i>"
        )

        share_btn = InlineKeyboardButton(
            text="📢 Поделиться с другом",
            url=f"https://t.me/share/url?url={ref_link}&text=Попробуй%20быстрый%20и%20неблокируемый%20VLESS%20VPN%20NexusVPN!%20Дают%203%20дня%20бесплатно%20⚡",
        )

        await query.message.answer(
            text=text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[share_btn]]),
            parse_mode=ParseMode.HTML,
        )
        await query.answer()


@router.callback_query(F.data == "guide:menu")
async def callback_guide_menu(query: CallbackQuery):
    """Display instructions menu."""
    await query.message.answer(
        "📱 <b>Инструкции по настройке NexusVPN</b>\n\n"
        "Мы поддерживаем все популярные клиенты с поддержкой современного протокола VLESS Reality:\n\n"
        "• <b>Happ Proxy Utility</b> (Рекомендуется для iOS / Android — стильный, простой)\n"
        "• <b>v2rayNG</b> (Классический быстрый клиент для Android)\n"
        "• <b>AmneziaVPN</b> (Открытый клиент для Windows, macOS, Linux, iOS, Android)\n"
        "• <b>Streisand / Shadowrocket</b> (iOS)\n\n"
        "Выберите вашу платформу для детальной инструкции:",
        reply_markup=get_guides_keyboard(),
        parse_mode=ParseMode.HTML,
    )
    await query.answer()


@router.callback_query(F.data == "guide:ios")
async def callback_guide_ios(query: CallbackQuery):
    """iOS installation guide."""
    text = (
        "🍏 <b>Инструкция для iPhone / iPad:</b>\n\n"
        "1. Установите бесплатное приложение <b>Happ Proxy Utility</b> или <b>Streisand</b> из App Store.\n"
        "2. Скопируйте ваш VLESS ключ из меню бота (кнопка <i>«🔑 Мой ключ VLESS»</i>) или добавьте ссылку на подписку.\n"
        "3. Откройте приложение, нажмите <b>«+»</b> в правом верхнем углу и выберите <b>«Import from clipboard»</b> (Вставить из буфера).\n"
        "4. Разрешите добавление VPN-конфигурации в настройках iOS.\n"
        "5. Нажмите кнопку включения (Connect). Готово! Вы в безопасном интернете."
    )
    await query.message.answer(text, parse_mode=ParseMode.HTML)
    await query.answer()


@router.callback_query(F.data == "guide:android")
async def callback_guide_android(query: CallbackQuery):
    """Android installation guide."""
    text = (
        "🤖 <b>Инструкция для Android:</b>\n\n"
        "1. Установите <b>v2rayNG</b> или <b>Happ</b> из Google Play / GitHub.\n"
        "2. Скопируйте ваш VLESS ключ.\n"
        "3. В приложении v2rayNG нажмите значок <b>«+»</b> вверху экрана -> <b>«Импортировать конфигурацию из буфера обмена»</b>.\n"
        "4. Выберите добавленный сервер и нажмите круглую кнопку подключения внизу экрана."
    )
    await query.message.answer(text, parse_mode=ParseMode.HTML)
    await query.answer()


@router.callback_query(F.data == "guide:desktop")
async def callback_guide_desktop(query: CallbackQuery):
    """PC/Mac installation guide."""
    text = (
        "💻 <b>Инструкция для Windows / macOS:</b>\n\n"
        "• <b>AmneziaVPN:</b> Скачайте с amnezia.org, нажмите «Настроить свой протокол» или импортируйте VLESS ключ.\n"
        "• <b>v2rayN (Windows):</b> Скачайте v2rayN, скопируйте VLESS ключ, нажмите Ctrl+V в окне программы и активируйте системный прокси.\n"
        "• <b>FoXray / V2box (macOS):</b> Доступны в Mac App Store, поддерживают автообновление по подписке."
    )
    await query.message.answer(text, parse_mode=ParseMode.HTML)
    await query.answer()


@router.callback_query(F.data == "balance:topup")
async def callback_balance_topup(query: CallbackQuery):
    """Quick balance top-up info."""
    user_id = query.from_user.id
    async with async_session_factory() as session:
        user = (await session.execute(select(User).where(User.telegram_id == user_id))).scalar_one_or_none()
        ref_code = user.ref_code if user else "app"

    await query.message.answer(
        "💳 <b>Пополнение баланса NexusVPN</b>\n\n"
        "Пополнить баланс банковской картой (МИР, Visa, Mastercard, СБП) или криптовалютой можно прямо в нашем <b>Telegram Mini App</b>!\n\n"
        "Средства зачисляются мгновенно.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="⚡ Открыть Mini App для пополнения", web_app=WebAppInfo(url=f"{WEBAPP_URL}?ref={ref_code}"))]
            ]
        ),
        parse_mode=ParseMode.HTML,
    )
    await query.answer()


# --------------------------------------------------------------------------
# Bot Initialization Runner
# --------------------------------------------------------------------------

async def start_bot():
    """Starts the polling loop for aiogram 3.x bot."""
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_router(router)

    # Initialize tables
    await init_db()
    logger.info("Bot starting polling...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(start_bot())
