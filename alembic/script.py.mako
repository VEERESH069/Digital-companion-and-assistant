"""Script template for migration template.
Imports, environment setup, etc. is already done by Alembic."""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'MIGRATION_REVISION'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade: Apply the migration"""
    pass


def downgrade() -> None:
    """Downgrade: Revert the migration"""
    pass
