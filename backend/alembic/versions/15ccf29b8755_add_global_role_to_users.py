"""add global role to users

Revision ID: 15ccf29b8755
Revises: 88dcf3749f70
Create Date: 2026-09-26 16:24:05.632845

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '15ccf29b8755'
down_revision: Union[str, Sequence[str], None] = '88dcf3749f70'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    global_role_enum = sa.Enum(
        "PLATFORM_ADMIN",
        name="globalrole",
    )

    global_role_enum.create(op.get_bind())

    op.add_column(
        "users",
        sa.Column(
            "global_role",
            global_role_enum,
            nullable=True,
        ),
    )

def downgrade() -> None:
    """Downgrade schema."""
    global_role_enum = sa.Enum(
        "PLATFORM_ADMIN",
        name="globalrole",
    )

    op.drop_column(
        "users",
        "global_role",
    )

    global_role_enum.drop(op.get_bind())
