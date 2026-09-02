"""Add project ownership

Revision ID: 202603120003
Revises: 202603120002
Create Date: 2026-03-12 00:02:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "202603120003"
down_revision: Union[str, Sequence[str], None] = "202603120002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("projects")}
    foreign_keys = inspector.get_foreign_keys("projects")
    has_owner_foreign_key = any(
        foreign_key["constrained_columns"] == ["owner_id"]
        and foreign_key["referred_table"] == "users"
        and foreign_key["referred_columns"] == ["id"]
        for foreign_key in foreign_keys
    )

    with op.batch_alter_table("projects", recreate="auto") as batch_op:
        if "owner_id" not in columns:
            batch_op.add_column(sa.Column("owner_id", sa.Uuid(), nullable=True))

        if not has_owner_foreign_key:
            batch_op.create_foreign_key(
                "fk_projects_owner_id_users",
                "users",
                ["owner_id"],
                ["id"],
            )


def downgrade() -> None:
    pass