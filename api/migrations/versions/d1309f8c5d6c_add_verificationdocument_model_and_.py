"""Add VerificationDocument model and relationship to Property

Revision ID: d1309f8c5d6c
Revises: 71d6e0e033f3
Create Date: 2025-04-05 01:29:40.574345

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd1309f8c5d6c'
down_revision: Union[str, None] = '71d6e0e033f3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###
