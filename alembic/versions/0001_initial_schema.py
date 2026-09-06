"""initial_schema

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-09-06 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('telegram_id', sa.BigInteger(), nullable=False),
        sa.Column('username', sa.String(length=128), nullable=True),
        sa.Column('first_name', sa.String(length=128), nullable=True),
        sa.Column('balance', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('ref_code', sa.String(length=32), nullable=False),
        sa.Column('invited_by', sa.Integer(), nullable=True),
        sa.Column('free_trial_used', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('marzban_username', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['invited_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_marzban_username'), 'users', ['marzban_username'], unique=True)
    op.create_index(op.f('ix_users_ref_code'), 'users', ['ref_code'], unique=True)
    op.create_index(op.f('ix_users_telegram_id'), 'users', ['telegram_id'], unique=True)

    # Create subscriptions table
    op.create_table(
        'subscriptions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('plan_name', sa.String(length=64), nullable=False),
        sa.Column('traffic_limit_bytes', sa.BigInteger(), server_default='0', nullable=False),
        sa.Column('start_date', sa.DateTime(), nullable=False),
        sa.Column('end_date', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('subscription_url', sa.String(length=512), nullable=True),
        sa.Column('vless_link', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_subscriptions_id'), 'subscriptions', ['id'], unique=False)

    # Create referrals table
    op.create_table(
        'referrals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('referrer_id', sa.Integer(), nullable=False),
        sa.Column('referee_id', sa.Integer(), nullable=False),
        sa.Column('reward_amount', sa.Float(), server_default='100.0', nullable=False),
        sa.Column('is_paid', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['referee_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['referrer_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_referrals_id'), 'referrals', ['id'], unique=False)

    # Create payment_transactions table
    op.create_table(
        'payment_transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('gateway', sa.String(length=32), nullable=False),
        sa.Column('invoice_id', sa.String(length=128), nullable=False),
        sa.Column('amount_rub', sa.Float(), nullable=False),
        sa.Column('status', sa.String(length=32), server_default='pending', nullable=False),
        sa.Column('pay_url', sa.String(length=512), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payment_transactions_id'), 'payment_transactions', ['id'], unique=False)
    op.create_index(op.f('ix_payment_transactions_invoice_id'), 'payment_transactions', ['invoice_id'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_payment_transactions_invoice_id'), table_name='payment_transactions')
    op.drop_index(op.f('ix_payment_transactions_id'), table_name='payment_transactions')
    op.drop_table('payment_transactions')
    op.drop_index(op.f('ix_referrals_id'), table_name='referrals')
    op.drop_table('referrals')
    op.drop_index(op.f('ix_subscriptions_id'), table_name='subscriptions')
    op.drop_table('subscriptions')
    op.drop_index(op.f('ix_users_telegram_id'), table_name='users')
    op.drop_index(op.f('ix_users_ref_code'), table_name='users')
    op.drop_index(op.f('ix_users_marzban_username'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_table('users')
