"""add slug to systems

Revision ID: fac5c65eab81
Revises: 6c43cdca9088
Create Date: 2026-09-08 22:41:50.286536

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fac5c65eab81'
down_revision: Union[str, Sequence[str], None] = '6c43cdca9088'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # SQLite не поддерживает ALTER для добавления unique-constraint,
    # поэтому используем batch mode (copy-and-move стратегию).
    with op.batch_alter_table('systems') as batch_op:
        batch_op.add_column(
            sa.Column('slug', sa.String(length=50), nullable=True)
        )
        batch_op.create_unique_constraint(
            'uq_systems_slug',
            ['slug'],
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('systems') as batch_op:
        batch_op.drop_constraint(
            'uq_systems_slug',
            type_='unique',
        )
        batch_op.drop_column('slug')