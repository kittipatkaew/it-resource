"""Add assignees field to tasks table for multiple assignees

Revision ID: add_assignees_to_tasks
Revises: add_delivery_date_to_projects
Create Date: 2026-02-28

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_assignees_to_tasks'
down_revision = 'add_delivery_date_to_projects'
branch_labels = None
depends_on = None


def upgrade():
    # Add assignees column as JSON to tasks table
    op.add_column('tasks', sa.Column('assignees', sa.JSON(), nullable=True))
    
    # Migrate existing single assignee data to assignees array
    # For PostgreSQL, use this syntax
    op.execute("""
        UPDATE tasks 
        SET assignees = jsonb_build_array(assignee_name)
        WHERE assignee_name IS NOT NULL
    """)
    
    # For tasks without assignee, set empty array
    op.execute("""
        UPDATE tasks 
        SET assignees = '[]'::jsonb
        WHERE assignee_name IS NULL OR assignees IS NULL
    """)


def downgrade():
    # Remove assignees column
    op.drop_column('tasks', 'assignees')
