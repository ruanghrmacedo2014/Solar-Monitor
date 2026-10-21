"""add action to ticket message edit history

Revision ID: 6e5b514a05f9
Revises: 3fe06b94dd46
Create Date: 2026-10-02 07:49:41.305863

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6e5b514a05f9'
down_revision: Union[str, Sequence[str], None] = '3fe06b94dd46'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    ticket_message_history_action = sa.Enum(
        "EDITED",
        "DELETED",
        name="ticket_message_history_action",
    )

    ticket_message_history_action.create(
        op.get_bind(),
        checkfirst=True,
    )

    op.add_column(
        "ticket_message_edit_history",
        sa.Column(
            "action",
            ticket_message_history_action,
            nullable=True,
        ),
    )

    op.execute(
        """
        UPDATE ticket_message_edit_history
        SET action = 'EDITED'
        WHERE action IS NULL
        """
    )

    op.alter_column(
        "ticket_message_edit_history",
        "action",
        nullable=False,
    )


def downgrade() -> None:
    op.drop_column(
        "ticket_message_edit_history",
        "action",
    )

    sa.Enum(
        "EDITED",
        "DELETED",
        name="ticket_message_history_action",
    ).drop(
        op.get_bind(),
        checkfirst=True,
    )
