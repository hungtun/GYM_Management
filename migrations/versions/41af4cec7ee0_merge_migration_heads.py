"""merge migration heads

Revision ID: 41af4cec7ee0
Revises: 3654940eda12, f3f2269dfb5a
Create Date: 2025-12-19 22:18:21.503634

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '41af4cec7ee0'
down_revision = ('3654940eda12', 'f3f2269dfb5a')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
