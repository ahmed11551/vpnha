"""
Centralized configuration management for NexusVPN ecosystem.
Uses Pydantic Settings when installed, with automatic fallback to standard environment parsing.
Provides a unified, type-safe settings singleton across database, services, bot, and api.
"""

import os
from typing import List, Optional

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
    from pydantic import Field

    class Settings(BaseSettings):
        model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            extra="ignore",
        )

        # Core & Server
        APP_NAME: str = "NexusVPN"
        DEBUG: bool = False
        SECRET_KEY: str = "generate-a-strong-random-secret-key-for-production"

        # Telegram Bot & Mini App
        BOT_TOKEN: str = "123456789:ABCdefGHIjklMNOpqrSTUvwxYZ"
        BOT_USERNAME: str = "asbvpn_bot"
        WEBAPP_URL: str = "https://vpn.yourdomain.com/mini-app"

        # Security & CORS
        ALLOWED_ORIGINS: str = "https://t.me,https://web.telegram.org,http://localhost:3000,http://127.0.0.1:3000"
        ALLOW_INSECURE_TEST_AUTH: bool = True
        MAX_AUTH_AGE_SECONDS: int = 86400  # 24 hours

        # Database Configuration (PostgreSQL / SQLite)
        DATABASE_URL: str = "sqlite+aiosqlite:///./vpn_service.db"
        SQL_DEBUG: bool = False

        # Marzban Panel API (Xray VLESS + Reality)
        MARZBAN_HOST: str = "https://marzban.yourdomain.com:8000"
        MARZBAN_USERNAME: str = "admin"
        MARZBAN_PASSWORD: str = "strong_admin_password"
        MARZBAN_VERIFY_SSL: bool = True
        MARZBAN_CA_BUNDLE: Optional[str] = None

        # Payment Gateways
        CRYPTO_BOT_TOKEN: Optional[str] = None
        CRYPTO_BOT_NET: str = "mainnet"
        YOOKASSA_SHOP_ID: Optional[str] = None
        YOOKASSA_SECRET_KEY: Optional[str] = None

        # Commercial & Referral Logic
        FREE_TRIAL_DAYS: int = 3
        TRIAL_TRAFFIC_GB: int = 5
        REFERRAL_BONUS_RUB: float = 100.0
        REFERRAL_COMMISSION_PERCENT: float = 15.0

        # Administration
        ADMIN_IDS: str = "123456789"

        @property
        def cors_origins(self) -> List[str]:
            return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

        @property
        def admin_ids_list(self) -> List[int]:
            return [int(x.strip()) for x in self.ADMIN_IDS.split(",") if x.strip().isdigit()]

    settings = Settings()

except ImportError:
    # Graceful fallback when pydantic_settings is not installed in the current environment
    class FallbackSettings:
        def __init__(self):
            self.APP_NAME: str = os.getenv("APP_NAME", "NexusVPN")
            self.DEBUG: bool = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")
            self.SECRET_KEY: str = os.getenv("SECRET_KEY", "generate-a-strong-random-secret-key-for-production")

            self.BOT_TOKEN: str = os.getenv("BOT_TOKEN", "123456789:ABCdefGHIjklMNOpqrSTUvwxYZ")
            self.BOT_USERNAME: str = os.getenv("BOT_USERNAME", "asbvpn_bot")
            self.WEBAPP_URL: str = os.getenv("WEBAPP_URL", "https://vpn.yourdomain.com/mini-app")

            self.ALLOWED_ORIGINS: str = os.getenv(
                "ALLOWED_ORIGINS",
                "https://t.me,https://web.telegram.org,http://localhost:3000,http://127.0.0.1:3000"
            )
            self.ALLOW_INSECURE_TEST_AUTH: bool = os.getenv("ALLOW_INSECURE_TEST_AUTH", "true").lower() in ("true", "1", "yes")
            self.MAX_AUTH_AGE_SECONDS: int = int(os.getenv("MAX_AUTH_AGE_SECONDS", "86400"))

            self.DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./vpn_service.db")
            self.SQL_DEBUG: bool = os.getenv("SQL_DEBUG", "false").lower() in ("true", "1", "yes")

            self.MARZBAN_HOST: str = os.getenv("MARZBAN_HOST", "https://marzban.yourdomain.com:8000")
            self.MARZBAN_USERNAME: str = os.getenv("MARZBAN_USERNAME", "admin")
            self.MARZBAN_PASSWORD: str = os.getenv("MARZBAN_PASSWORD", "strong_admin_password")
            self.MARZBAN_VERIFY_SSL: bool = os.getenv("MARZBAN_VERIFY_SSL", "true").lower() not in ("false", "0", "no")
            self.MARZBAN_CA_BUNDLE: Optional[str] = os.getenv("MARZBAN_CA_BUNDLE")

            self.CRYPTO_BOT_TOKEN: Optional[str] = os.getenv("CRYPTO_BOT_TOKEN")
            self.CRYPTO_BOT_NET: str = os.getenv("CRYPTO_BOT_NET", "mainnet")
            self.YOOKASSA_SHOP_ID: Optional[str] = os.getenv("YOOKASSA_SHOP_ID")
            self.YOOKASSA_SECRET_KEY: Optional[str] = os.getenv("YOOKASSA_SECRET_KEY")

            self.FREE_TRIAL_DAYS: int = int(os.getenv("FREE_TRIAL_DAYS", "3"))
            self.TRIAL_TRAFFIC_GB: int = int(os.getenv("TRIAL_TRAFFIC_GB", "5"))
            self.REFERRAL_BONUS_RUB: float = float(os.getenv("REFERRAL_BONUS_RUB", "100.0"))
            self.REFERRAL_COMMISSION_PERCENT: float = float(os.getenv("REFERRAL_COMMISSION_PERCENT", "15.0"))
            self.ADMIN_IDS: str = os.getenv("ADMIN_IDS", "123456789")

        @property
        def cors_origins(self) -> List[str]:
            return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

        @property
        def admin_ids_list(self) -> List[int]:
            return [int(x.strip()) for x in self.ADMIN_IDS.split(",") if x.strip().isdigit()]

    settings = FallbackSettings()
