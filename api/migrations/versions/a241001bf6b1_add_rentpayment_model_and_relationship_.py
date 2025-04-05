"""Add RentPayment model and relationship to Lease

Revision ID: a241001bf6b1
Revises: 3719c2b07592
Create Date: 2025-04-05 09:02:23.828630

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a241001bf6b1'
down_revision: Union[str, None] = '3719c2b07592'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('reviews',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('rating', sa.Integer(), nullable=False),
    sa.Column('comment', sa.Text(), nullable=True),
    sa.Column('reviewer_id', sa.Uuid(), nullable=False),
    sa.Column('agent_id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.CheckConstraint('rating >= 1 AND rating <= 5', name=op.f('ck_reviews_review_rating_check')),
    sa.ForeignKeyConstraint(['agent_id'], ['users.id'], name=op.f('fk_reviews_agent_id_users')),
    sa.ForeignKeyConstraint(['reviewer_id'], ['users.id'], name=op.f('fk_reviews_reviewer_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_reviews')),
    sa.UniqueConstraint('reviewer_id', 'agent_id', name='uq_review_per_agent')
    )
    with op.batch_alter_table('reviews', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_reviews_agent_id'), ['agent_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_reviews_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_reviews_reviewer_id'), ['reviewer_id'], unique=False)

    op.create_table('rent_payments',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('lease_id', sa.UUID(), nullable=False),
    sa.Column('amount_due', sa.Float(), nullable=False),
    sa.Column('amount_paid', sa.Float(), nullable=True),
    sa.Column('due_date', sa.Date(), nullable=False),
    sa.Column('payment_date', sa.Date(), nullable=True),
    sa.Column('status', sa.Enum('PENDING', 'PAID', 'OVERDUE', 'PARTIAL', 'CANCELLED', name='rentpaymentstatus'), nullable=False),
    sa.Column('payment_method', sa.Enum('CASH', 'BANK_TRANSFER', 'MOBILE_MONEY_MTN', 'MOBILE_MONEY_ORANGE', 'CARD', 'OTHER', 'UNKNOWN', name='paymentmethod'), nullable=True),
    sa.Column('transaction_reference', sa.String(), nullable=True),
    sa.Column('notes', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['lease_id'], ['leases.id'], name=op.f('fk_rent_payments_lease_id_leases')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_rent_payments'))
    )
    with op.batch_alter_table('rent_payments', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_rent_payments_due_date'), ['due_date'], unique=False)
        batch_op.create_index(batch_op.f('ix_rent_payments_lease_id'), ['lease_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_rent_payments_status'), ['status'], unique=False)

    with op.batch_alter_table('lease_agreement_templates', schema=None) as batch_op:
        batch_op.alter_column('id',
               existing_type=sa.NUMERIC(),
               type_=sa.UUID(),
               existing_nullable=False)

    with op.batch_alter_table('leases', schema=None) as batch_op:
        batch_op.alter_column('id',
               existing_type=sa.NUMERIC(),
               type_=sa.UUID(),
               existing_nullable=False)

    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('leases', schema=None) as batch_op:
        batch_op.alter_column('id',
               existing_type=sa.UUID(),
               type_=sa.NUMERIC(),
               existing_nullable=False)

    with op.batch_alter_table('lease_agreement_templates', schema=None) as batch_op:
        batch_op.alter_column('id',
               existing_type=sa.UUID(),
               type_=sa.NUMERIC(),
               existing_nullable=False)

    with op.batch_alter_table('rent_payments', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_rent_payments_status'))
        batch_op.drop_index(batch_op.f('ix_rent_payments_lease_id'))
        batch_op.drop_index(batch_op.f('ix_rent_payments_due_date'))

    op.drop_table('rent_payments')
    with op.batch_alter_table('reviews', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_reviews_reviewer_id'))
        batch_op.drop_index(batch_op.f('ix_reviews_id'))
        batch_op.drop_index(batch_op.f('ix_reviews_agent_id'))

    op.drop_table('reviews')
    # ### end Alembic commands ###
