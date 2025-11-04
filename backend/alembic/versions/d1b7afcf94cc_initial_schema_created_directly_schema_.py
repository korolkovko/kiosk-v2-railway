# script.py.mako
# Alembic revision script template

"""Initial schema created directly - Schema from models.py - 20251103_172733

Revision ID: d1b7afcf94cc
Revises: 
Create Date: 2025-11-03 17:27:34.633265

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd1b7afcf94cc'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade database schema"""
    pass


def downgrade() -> None:
    """Downgrade database schema"""
    pass