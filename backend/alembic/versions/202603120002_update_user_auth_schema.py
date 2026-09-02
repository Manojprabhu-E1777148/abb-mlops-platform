"""Update user authentication schema

Revision ID: 202603120002
Revises: 202603120001
Create Date: 2026-03-12 00:01:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "202603120002"
down_revision: Union[str, Sequence[str], None] = "202603120001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("users", recreate="auto") as batch_op:
        batch_op.alter_column(
            "hashed_password",
            new_column_name="password_hash",
            existing_type=sa.String(),
            existing_nullable=False,
        )
        batch_op.add_column(
            sa.Column(
                "role",
                sa.String(),
                nullable=False,
                server_default="member",
            )
        )
        batch_op.add_column(
            sa.Column(
                "is_active",
                sa.Boolean(),
                nullable=False,
                server_default=sa.true(),
            )
        )
        batch_op.create_check_constraint(
            "ck_users_role",
            "role IN ('admin', 'member')",
        )


def downgrade() -> None:
    with op.batch_alter_table("users", recreate="auto") as batch_op:
        batch_op.drop_constraint("ck_users_role", type_="check")
        batch_op.drop_column("is_active")
        batch_op.drop_column("role")
        batch_op.alter_column(
            "password_hash",
            new_column_name="hashed_password",
            existing_type=sa.String(),
            existing_nullable=False,
        )