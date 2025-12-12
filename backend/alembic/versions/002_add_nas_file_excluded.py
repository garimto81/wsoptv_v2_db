"""Add is_excluded and exclude_reason to nas_files

Revision ID: 002
Revises: 001
Create Date: 2025-12-12

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add is_excluded column (default False)
    op.add_column(
        "nas_files",
        sa.Column("is_excluded", sa.Boolean(), nullable=False, server_default="false"),
        schema="pokervod",
    )

    # Add exclude_reason column
    op.add_column(
        "nas_files",
        sa.Column("exclude_reason", sa.String(100), nullable=True),
        schema="pokervod",
    )

    # Create index for filtering excluded files
    op.create_index(
        "ix_nas_files_is_excluded",
        "nas_files",
        ["is_excluded"],
        schema="pokervod",
    )


def downgrade() -> None:
    op.drop_index("ix_nas_files_is_excluded", table_name="nas_files", schema="pokervod")
    op.drop_column("nas_files", "exclude_reason", schema="pokervod")
    op.drop_column("nas_files", "is_excluded", schema="pokervod")
