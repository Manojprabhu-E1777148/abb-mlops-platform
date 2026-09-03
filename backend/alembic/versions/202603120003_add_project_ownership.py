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

    if "owner_id" not in columns:
        op.add_column("projects", sa.Column("owner_id", sa.Uuid(), nullable=True))

    unowned_project_count = bind.execute(
        sa.text("SELECT count(*) FROM projects WHERE owner_id IS NULL")
    ).scalar_one()

    if "owner" in columns and unowned_project_count:
        if bind.dialect.name == "mssql":
            backfill_statement = """
                UPDATE project
                SET owner_id = matched_user.id
                FROM projects AS project
                INNER JOIN users AS matched_user
                    ON lower(ltrim(rtrim(project.owner))) = lower(ltrim(rtrim(matched_user.full_name)))
                WHERE project.owner_id IS NULL
                  AND project.owner IS NOT NULL
                  AND (
                      SELECT count(*)
                      FROM users AS candidate_user
                      WHERE lower(ltrim(rtrim(candidate_user.full_name))) = lower(ltrim(rtrim(project.owner)))
                  ) = 1
                """
        else:
            backfill_statement = """
                UPDATE projects AS project
                SET owner_id = matched_user.id
                FROM users AS matched_user
                WHERE project.owner_id IS NULL
                  AND project.owner IS NOT NULL
                  AND lower(btrim(project.owner)) = lower(btrim(matched_user.full_name))
                  AND (
                      SELECT count(*)
                      FROM users AS candidate_user
                      WHERE lower(btrim(candidate_user.full_name)) = lower(btrim(project.owner))
                  ) = 1
                """

        bind.execute(sa.text(backfill_statement))
        unowned_project_count = bind.execute(
            sa.text("SELECT count(*) FROM projects WHERE owner_id IS NULL")
        ).scalar_one()

    if unowned_project_count:
        raise RuntimeError(
            "Cannot migrate project ownership: one or more legacy owner values do not "
            "map uniquely to a user. Resolve those records and rerun the migration."
        )

    inspector = sa.inspect(bind)
    foreign_keys = inspector.get_foreign_keys("projects")
    has_owner_foreign_key = any(
        foreign_key["constrained_columns"] == ["owner_id"]
        and foreign_key["referred_table"] == "users"
        and foreign_key["referred_columns"] == ["id"]
        for foreign_key in foreign_keys
    )

    with op.batch_alter_table("projects", recreate="auto") as batch_op:
        if not has_owner_foreign_key:
            batch_op.create_foreign_key(
                "fk_projects_owner_id_users",
                "users",
                ["owner_id"],
                ["id"],
            )

        batch_op.alter_column(
            "owner_id",
            existing_type=sa.Uuid(),
            nullable=False,
        )

        if "owner" in columns:
            batch_op.drop_column("owner")


def downgrade() -> None:
    raise NotImplementedError("Project ownership migration is intentionally irreversible.")
