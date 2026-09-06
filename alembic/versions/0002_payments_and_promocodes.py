"""payments_and_promocodes

Revision ID: 0002_payments_and_promocodes
Revises: 0001_initial_schema
Create Date: 2026-09-06 13:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0002_payments_and_promocodes'
down_revision: Union[str, None] = '0001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create promocodes table
    op.create_table(
        'promocodes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=64), nullable=False),
        sa.Column('discount_percent', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('bonus_days', sa.Integer(), server_default='0', nullable=False),
        sa.Column('bonus_rub', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('max_activations', sa.Integer(), server_default='100', nullable=False),
        sa.Column('current_activations', sa.Integer(), server_default='0', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_promocodes_code'), 'promocodes', ['code'], unique=True)
    op.create_index(op.f('ix_promocodes_is_active'), 'promocodes', ['is_active'], unique=False)

    # Create payments table (or alter payment_transactions)
    op.create_table(
        'payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.String(length=64), nullable=False),
        sa.Column('gateway', sa.String(length=32), server_default='cryptobot', nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(length=16), server_default='RUB', nullable=False),
        sa.Column('status', sa.String(length=32), server_default='pending', nullable=False),
        sa.Column('plan_id', sa.String(length=32), nullable=True),
        sa.Column('promo_code_id', sa.Integer(), nullable=True),
        sa.Column('external_invoice_id', sa.String(length=128), nullable=True),
        sa.Column('pay_url', sa.String(length=512), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('paid_at', sa.DateTime(), nullable=True),
        sa.Column('meta_data', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['promo_code_id'], ['promocodes.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payments_order_id'), 'payments', ['order_id'], unique=True)
    op.create_index(op.f('ix_payments_status'), 'payments', ['status'], unique=False)
    op.create_index(op.f('ix_payments_gateway'), 'payments', ['gateway'], unique=False)
    op.create_index(op.f('ix_payments_user_id'), 'payments', ['user_id'], unique=False)
    op.create_index(op.f('ix_payments_external_invoice_id'), 'payments', ['external_invoice_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_payments_external_invoice_id'), table_name='payments')
    op.drop_index(op.f('ix_payments_user_id'), table_name='payments')
    op.drop_index(op.f('ix_payments_gateway'), table_name='payments')
    op.drop_index(op.f('ix_payments_status'), table_name='payments')
    op.drop_index(op.f('ix_payments_order_id'), table_name='payments')
    op.drop_table('payments')

    op.drop_index(op.f('ix_promocodes_is_active'), table_name='promocodes')
    op.drop_index(op.f('ix_promocodes_code'), table_name='promocodes')
    op.drop_table('promocodes')
