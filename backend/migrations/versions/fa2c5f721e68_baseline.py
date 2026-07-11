"""baseline

Revision ID: fa2c5f721e68
Revises: 
Create Date: 2026-07-11 10:32:47.138399

"""
from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = 'fa2c5f721e68'
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
