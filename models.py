"""
SQLAlchemy ORM models for VPN commercial ecosystem:
User, Subscription, Referral, PromoCode, and Payment.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    username: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    balance: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    ref_code: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    invited_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    free_trial_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    marzban_username: Mapped[Optional[str]] = mapped_column(String(64), unique=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    subscriptions: Mapped[List["Subscription"]] = relationship(
        "Subscription", back_populates="user", cascade="all, delete-orphan"
    )
    invited_users: Mapped[List["User"]] = relationship(
        "User", backref="inviter", remote_side=[id]
    )
    referral_earnings: Mapped[List["Referral"]] = relationship(
        "Referral",
        foreign_keys="[Referral.referrer_id]",
        back_populates="referrer",
        cascade="all, delete-orphan",
    )
    payments: Mapped[List["Payment"]] = relationship(
        "Payment", back_populates="user", cascade="all, delete-orphan"
    )

    @property
    def transactions(self) -> List["Payment"]:
        """Backward compatibility alias."""
        return self.payments


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    plan_name: Mapped[str] = mapped_column(String(64), default="Standart", nullable=False)
    traffic_limit_bytes: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)  # 0 = unlimited
    used_traffic_bytes: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    start_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True, nullable=False)
    subscription_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    vless_link: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="subscriptions")


class Referral(Base):
    __tablename__ = "referrals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    referrer_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    referee_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    reward_amount: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    is_paid: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    referrer: Mapped["User"] = relationship("User", foreign_keys=[referrer_id], back_populates="referral_earnings")
    referee: Mapped["User"] = relationship("User", foreign_keys=[referee_id])


class PromoCode(Base):
    __tablename__ = "promocodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    discount_percent: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    bonus_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    bonus_rub: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    max_activations: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    current_activations: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True, nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    payments: Mapped[List["Payment"]] = relationship("Payment", back_populates="promo_code")


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    order_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    gateway: Mapped[str] = mapped_column(String(32), default="cryptobot", index=True, nullable=False)  # cryptobot, stars, yookassa
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(16), default="RUB", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True, nullable=False)  # pending, paid, expired, failed
    plan_id: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)  # if direct plan purchase
    promo_code_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("promocodes.id"), nullable=True)
    external_invoice_id: Mapped[Optional[str]] = mapped_column(String(128), index=True, nullable=True)
    pay_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    meta_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON-string with extra provider data

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="payments")
    promo_code: Mapped[Optional["PromoCode"]] = relationship("PromoCode", back_populates="payments")


# Backward compatibility alias
PaymentTransaction = Payment
