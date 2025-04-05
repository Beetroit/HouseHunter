"""Add MaintenanceRequest model and relationships2

Revision ID: 5384140aa0ba
Revises: 08e30345951a
Create Date: 2025-04-05 09:31:15.342464

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5384140aa0ba'
down_revision: Union[str, None] = '08e30345951a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('maintenance_requests',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('property_id', sa.Uuid(), nullable=False),
    sa.Column('tenant_id', sa.Uuid(), nullable=False),
    sa.Column('landlord_id', sa.Uuid(), nullable=False),
    sa.Column('title', sa.String(length=200), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('photo_url', sa.String(length=512), nullable=True),
    sa.Column('status', sa.Enum('SUBMITTED', 'IN_PROGRESS', 'RESOLVED', 'CLOSED', 'CANCELLED', name='maintenancerequeststatus'), nullable=False),
    sa.Column('resolution_notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['landlord_id'], ['users.id'], name=op.f('fk_maintenance_requests_landlord_id_users')),
    sa.ForeignKeyConstraint(['property_id'], ['properties.id'], name=op.f('fk_maintenance_requests_property_id_properties')),
    sa.ForeignKeyConstraint(['tenant_id'], ['users.id'], name=op.f('fk_maintenance_requests_tenant_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_maintenance_requests'))
    )
    with op.batch_alter_table('maintenance_requests', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_maintenance_requests_landlord_id'), ['landlord_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_maintenance_requests_property_id'), ['property_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_maintenance_requests_status'), ['status'], unique=False)
        batch_op.create_index(batch_op.f('ix_maintenance_requests_tenant_id'), ['tenant_id'], unique=False)

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

    with op.batch_alter_table('rent_payments', schema=None) as batch_op:
        batch_op.alter_column('id',
               existing_type=sa.NUMERIC(),
               type_=sa.UUID(),
               existing_nullable=False)
        batch_op.alter_column('lease_id',
               existing_type=sa.NUMERIC(),
               type_=sa.UUID(),
               existing_nullable=False)

    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('rent_payments', schema=None) as batch_op:
        batch_op.alter_column('lease_id',
               existing_type=sa.UUID(),
               type_=sa.NUMERIC(),
               existing_nullable=False)
        batch_op.alter_column('id',
               existing_type=sa.UUID(),
               type_=sa.NUMERIC(),
               existing_nullable=False)

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

    with op.batch_alter_table('maintenance_requests', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_maintenance_requests_tenant_id'))
        batch_op.drop_index(batch_op.f('ix_maintenance_requests_status'))
        batch_op.drop_index(batch_op.f('ix_maintenance_requests_property_id'))
        batch_op.drop_index(batch_op.f('ix_maintenance_requests_landlord_id'))

    op.drop_table('maintenance_requests')
    # ### end Alembic commands ###
