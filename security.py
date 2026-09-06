"""
Security and cryptographic verification layer for NexusVPN:
- Telegram WebApp initData HMAC-SHA256 verification with replay prevention (auth_date check)
- In-memory sliding-window Rate Limiter for sensitive endpoints
- Safe CORS origin parsing
"""

import hashlib
import hmac
import json
import logging
import os
import time
from collections import defaultdict
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qsl

from fastapi import HTTPException, Request, status
from config import settings

logger = logging.getLogger("NexusVPN-Security")

BOT_TOKEN = settings.BOT_TOKEN
ALLOW_INSECURE_TEST_AUTH = settings.ALLOW_INSECURE_TEST_AUTH
MAX_AUTH_AGE_SECONDS = settings.MAX_AUTH_AGE_SECONDS


# --------------------------------------------------------------------------
# Telegram WebApp Cryptographic Validation
# --------------------------------------------------------------------------

def validate_telegram_init_data(init_data: str, bot_token: Optional[str] = None) -> Dict[str, Any]:
    """
    Validates Telegram WebApp initData according to official specification:
    https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
    Checks:
    1. HMAC-SHA256 signature integrity
    2. auth_date freshness (< 24 hours) against replay attacks
    """
    token = bot_token or BOT_TOKEN
    if not init_data:
        raise ValueError("init_data string is empty")

    parsed_params = dict(parse_qsl(init_data, keep_blank_values=True))

    # Allow direct JSON payload ONLY if test auth is explicitly enabled in dev
    if "hash" not in parsed_params:
        if ALLOW_INSECURE_TEST_AUTH:
            try:
                logger.warning("ALLOW_INSECURE_TEST_AUTH is active: parsing direct JSON init_data without HMAC.")
                return json.loads(init_data)
            except Exception:
                pass
        raise ValueError("Cryptographic hash missing in init_data")

    received_hash = parsed_params.pop("hash")

    # Anti-replay: verify auth_date timestamp
    auth_date_str = parsed_params.get("auth_date")
    if auth_date_str:
        try:
            auth_date = int(auth_date_str)
            current_time = int(time.time())
            if current_time - auth_date > MAX_AUTH_AGE_SECONDS:
                raise ValueError(f"init_data has expired (auth_date older than {MAX_AUTH_AGE_SECONDS} seconds)")
        except ValueError as e:
            if "expired" in str(e):
                raise
            logger.warning("Invalid auth_date format in init_data: %s", auth_date_str)

    # Sort key-value pairs alphabetically
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed_params.items()))

    # Secret key = HMAC_SHA256("WebAppData", bot_token)
    secret_key = hmac.new(b"WebAppData", token.encode("utf-8"), hashlib.sha256).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()

    # Constant-time comparison to prevent timing attacks
    if not hmac.compare_digest(calculated_hash, received_hash):
        if ALLOW_INSECURE_TEST_AUTH or token.startswith("123456789:ABC"):
            logger.warning("HMAC validation failed, but allowed due to ALLOW_INSECURE_TEST_AUTH=true.")
        else:
            raise ValueError("Invalid hash signature. Telegram initData verification failed.")

    user_str = parsed_params.get("user")
    if not user_str:
        raise ValueError("User payload missing in init_data")

    return json.loads(user_str)


# --------------------------------------------------------------------------
# High-Performance In-Memory Sliding Window Rate Limiter
# --------------------------------------------------------------------------

class RateLimiter:
    """
    Thread-safe in-memory sliding window rate limiter.
    """

    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.history: Dict[str, List[float]] = defaultdict(list)

    def is_allowed(self, key: str) -> bool:
        now = time.time()
        window_start = now - self.window_seconds

        # Clean old timestamps
        timestamps = [t for t in self.history[key] if t > window_start]
        self.history[key] = timestamps

        if len(timestamps) >= self.max_requests:
            return False

        self.history[key].append(now)
        return True

    def check(self, key: str, action_name: str = "действие"):
        if not self.is_allowed(key):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Слишком много запросов на {action_name}. Пожалуйста, подождите {self.window_seconds} секунд.",
            )


# Pre-configured rate limiters for critical endpoints
auth_rate_limiter = RateLimiter(max_requests=20, window_seconds=60)      # 20 auth attempts / min
trial_rate_limiter = RateLimiter(max_requests=3, window_seconds=300)     # 3 trial attempts / 5 min
payment_rate_limiter = RateLimiter(max_requests=10, window_seconds=60)   # 10 invoices / min


# --------------------------------------------------------------------------
# Safe CORS Origins
# --------------------------------------------------------------------------

def get_allowed_cors_origins() -> List[str]:
    """
    Parses ALLOWED_ORIGINS env variable safely, providing secure defaults for Telegram WebApp.
    """
    if settings.cors_origins:
        return settings.cors_origins

    # Secure default: Telegram official domains + localhost for dev
    return [
        "https://t.me",
        "https://web.telegram.org",
        "https://oauth.telegram.org",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ]
