"""add delivery date to projects

Revision ID: add_delivery_date
Revises: ec57b5193cbd
Create Date: 2026-02-27 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_delivery_date'
down_revision = 'ec57b5193cbd'
branch_labels = None
depends_on = None


def upgrade():
    # Add delivery_date column to projects table
    op.add_column('projects', sa.Column('delivery_date', sa.Date(), nullable=True))


def downgrade():
    # Remove delivery_date column from projects table
    op.drop_column('projects', 'delivery_date')
