import { CodeFile } from '../types';

export const CODE_FILES: CodeFile[] = [
  {
    name: 'FastAPI Backend',
    filename: 'main.py',
    category: 'core',
    language: 'python',
    description: 'REST API, HMAC-SHA256 Telegram WebApp auth, subscriptions & referral commission engine',
    code: `"""
FastAPI Backend for NexusVPN Commercial Platform.
"""
from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import hmac, hashlib, json, secrets, time
from urllib.parse import parse_qsl
from datetime import datetime, timedelta

from database import get_db, init_db
from models import User, Subscription, Referral
from marzban_client import marzban_client

app = FastAPI(title="NexusVPN API", version="2.0.0")

# Full production implementation in /main.py`
  },
  {
    name: 'Marzban API Client',
    filename: 'marzban_client.py',
    category: 'core',
    language: 'python',
    description: 'Async httpx client for Marzban panel: VLESS Reality user provisioning, token caching, renewal',
    code: `"""
Production-grade Async API client for Marzban Panel (Xray / VLESS + Reality).
"""
import httpx, time, uuid, logging
from typing import Dict, Any, Optional

logger = logging.getLogger("MarzbanClient")

class MarzbanClient:
    def __init__(self, base_url=None, username=None, password=None):
        self.base_url = base_url
        self.username = username
        self.password = password
        self._token = None
        self._token_expires_at = 0.0

    async def get_access_token(self) -> str:
        # Authenticates via POST /api/admin/token
        ...

    async def create_user(self, username: str, expire_timestamp: int, data_limit_bytes: int = 0):
        # Provisions VLESS XTLS-Vision Reality client in Marzban
        ...`
  },
  {
    name: 'aiogram 3.x Telegram Bot',
    filename: 'bot.py',
    category: 'bot',
    language: 'python',
    description: 'Telegram bot with /start deep links, WebApp buttons, trial activation, and direct keys',
    code: `"""
Telegram Bot implementation on aiogram 3.x for NexusVPN.
"""
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from database import async_session_factory
from models import User, Subscription, Referral
from marzban_client import marzban_client

router = Router()

@router.message(CommandStart())
async def handle_start(message: Message, bot: Bot):
    # Extracts deep link referral code (/start ref_xxxx) and initializes user
    ...`
  },
  {
    name: 'Database Models',
    filename: 'models.py',
    category: 'database',
    language: 'python',
    description: 'SQLAlchemy 2.0 ORM schemas: User, Subscription, Referral with auto-linking',
    code: `"""
SQLAlchemy ORM models: User, Subscription, and Referral.
"""
from sqlalchemy import BigInteger, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str] = mapped_column(String(64), nullable=True)
    balance: Mapped[float] = mapped_column(Float, default=0.0)
    ref_code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    invited_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    free_trial_used: Mapped[bool] = mapped_column(Boolean, default=False)
    marzban_username: Mapped[str] = mapped_column(String(64), unique=True)`
  },
  {
    name: 'Database Engine',
    filename: 'database.py',
    category: 'database',
    language: 'python',
    description: 'Async SQLAlchemy connection pool for SQLite aiosqlite and PostgreSQL asyncpg',
    code: `"""
Database connection and session management using SQLAlchemy 2.0 (async).
"""
import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./vpn_service.db")
engine = create_async_engine(DATABASE_URL)
async_session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)`
  },
  {
    name: 'Telegram Mini App',
    filename: 'frontend/index.html',
    category: 'frontend',
    language: 'html',
    description: 'Standalone Mini App with Tailwind CSS + Alpine.js, live timer, VLESS key copy & QR code',
    code: `<!-- Full Telegram Mini App with Alpine.js + Tailwind CSS -->
<!-- Located at /frontend/index.html -->`
  },
  {
    name: 'Requirements & Docker',
    filename: 'requirements.txt',
    category: 'deployment',
    language: 'text',
    description: 'Dependencies list: FastAPI, aiogram 3, SQLAlchemy, httpx, uvicorn',
    code: `fastapi>=0.110.0
uvicorn[standard]>=0.28.0
sqlalchemy>=2.0.28
aiosqlite>=0.20.0
asyncpg>=0.29.0
aiogram>=3.4.1
httpx>=0.27.0
pydantic>=2.6.4`
  },
  {
    name: 'Server Setup Guide',
    filename: 'README.md',
    category: 'deployment',
    language: 'markdown',
    description: 'Complete step-by-step setup for Ubuntu 22/24, Marzban, Nginx, SSL, Systemd & Docker',
    code: `# NexusVPN Server Deployment Guide (Marzban Xray VLESS + Reality)
# Full instructions in /README.md`
  }
];
