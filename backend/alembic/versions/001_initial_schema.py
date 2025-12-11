"""Initial schema - 11 ORM models

Revision ID: 001
Revises:
Create Date: 2025-12-11

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 스키마 생성
    op.execute("CREATE SCHEMA IF NOT EXISTS pokervod")

    # 1. projects
    op.create_table(
        "projects",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("nas_base_path", sa.String(500), nullable=True),
        sa.Column("filename_pattern", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_projects"),
        sa.UniqueConstraint("code", name="uq_projects_code"),
        schema="pokervod",
    )
    op.create_index("ix_projects_code", "projects", ["code"], schema="pokervod")

    # 2. seasons
    op.create_table(
        "seasons",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("location", sa.String(200), nullable=True),
        sa.Column("sub_category", sa.String(50), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, default="active"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_seasons"),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["pokervod.projects.id"],
            name="fk_seasons_project_id_projects",
            ondelete="CASCADE",
        ),
        schema="pokervod",
    )
    op.create_index("ix_seasons_year", "seasons", ["year"], schema="pokervod")

    # 3. events
    op.create_table(
        "events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("season_id", sa.UUID(), nullable=False),
        sa.Column("event_number", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("name_short", sa.String(100), nullable=True),
        sa.Column("event_type", sa.String(50), nullable=True),
        sa.Column("game_type", sa.String(50), nullable=True),
        sa.Column("buy_in", sa.Numeric(10, 2), nullable=True),
        sa.Column("gtd_amount", sa.Numeric(15, 2), nullable=True),
        sa.Column("venue", sa.String(200), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, default="upcoming"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_events"),
        sa.ForeignKeyConstraint(
            ["season_id"],
            ["pokervod.seasons.id"],
            name="fk_events_season_id_seasons",
            ondelete="CASCADE",
        ),
        schema="pokervod",
    )
    op.create_index("ix_events_event_number", "events", ["event_number"], schema="pokervod")

    # 4. episodes
    op.create_table(
        "episodes",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("event_id", sa.UUID(), nullable=False),
        sa.Column("episode_number", sa.Integer(), nullable=True),
        sa.Column("day_number", sa.Integer(), nullable=True),
        sa.Column("part_number", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(500), nullable=True),
        sa.Column("episode_type", sa.String(50), nullable=True),
        sa.Column("table_type", sa.String(50), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_episodes"),
        sa.ForeignKeyConstraint(
            ["event_id"],
            ["pokervod.events.id"],
            name="fk_episodes_event_id_events",
            ondelete="CASCADE",
        ),
        schema="pokervod",
    )

    # 5. video_files
    op.create_table(
        "video_files",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("episode_id", sa.UUID(), nullable=True),
        sa.Column("file_path", sa.String(1000), nullable=False),
        sa.Column("file_name", sa.String(500), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("file_format", sa.String(20), nullable=True),
        sa.Column("file_mtime", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolution", sa.String(20), nullable=True),
        sa.Column("video_codec", sa.String(50), nullable=True),
        sa.Column("audio_codec", sa.String(50), nullable=True),
        sa.Column("bitrate_kbps", sa.Integer(), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("version_type", sa.String(20), nullable=True),
        sa.Column("is_original", sa.Boolean(), nullable=False, default=False),
        sa.Column("display_title", sa.String(500), nullable=True),
        sa.Column("content_type", sa.String(20), nullable=True),
        sa.Column("catalog_title", sa.String(300), nullable=True),
        sa.Column("is_catalog_item", sa.Boolean(), nullable=False, default=False),
        sa.Column("is_hidden", sa.Boolean(), nullable=False, default=False),
        sa.Column("hidden_reason", sa.String(50), nullable=True),
        sa.Column("scan_status", sa.String(20), nullable=False, default="pending"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_video_files"),
        sa.UniqueConstraint("file_path", name="uq_video_files_file_path"),
        sa.ForeignKeyConstraint(
            ["episode_id"],
            ["pokervod.episodes.id"],
            name="fk_video_files_episode_id_episodes",
            ondelete="SET NULL",
        ),
        schema="pokervod",
    )
    op.create_index("ix_video_files_file_path", "video_files", ["file_path"], schema="pokervod")

    # 6. tags
    op.create_table(
        "tags",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("name_display", sa.String(100), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, default=0),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_tags"),
        sa.UniqueConstraint("category", "name", name="uq_tags_category_name"),
        schema="pokervod",
    )
    op.create_index("ix_tags_category", "tags", ["category"], schema="pokervod")

    # 7. players
    op.create_table(
        "players",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("name_display", sa.String(200), nullable=True),
        sa.Column("nationality", sa.String(100), nullable=True),
        sa.Column("hendon_mob_id", sa.String(50), nullable=True),
        sa.Column("total_live_earnings", sa.Numeric(15, 2), nullable=True),
        sa.Column("wsop_bracelets", sa.Integer(), nullable=False, default=0),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_players"),
        sa.UniqueConstraint("name", name="uq_players_name"),
        schema="pokervod",
    )
    op.create_index("ix_players_name", "players", ["name"], schema="pokervod")

    # 8. hand_clips
    op.create_table(
        "hand_clips",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("episode_id", sa.UUID(), nullable=True),
        sa.Column("video_file_id", sa.UUID(), nullable=True),
        sa.Column("sheet_source", sa.String(50), nullable=True),
        sa.Column("sheet_row_number", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(500), nullable=True),
        sa.Column("timecode", sa.String(20), nullable=True),
        sa.Column("timecode_end", sa.String(20), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("hand_grade", sa.String(10), nullable=True),
        sa.Column("pot_size", sa.Integer(), nullable=True),
        sa.Column("winner_hand", sa.String(50), nullable=True),
        sa.Column("hands_involved", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_hand_clips"),
        sa.UniqueConstraint("sheet_source", "sheet_row_number", name="uq_hand_clips_sheet_source_row"),
        sa.ForeignKeyConstraint(
            ["episode_id"],
            ["pokervod.episodes.id"],
            name="fk_hand_clips_episode_id_episodes",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["video_file_id"],
            ["pokervod.video_files.id"],
            name="fk_hand_clips_video_file_id_video_files",
            ondelete="SET NULL",
        ),
        schema="pokervod",
    )
    op.create_index("ix_hand_clips_video_file_id", "hand_clips", ["video_file_id"], schema="pokervod")

    # 9. hand_clip_tags (N:N)
    op.create_table(
        "hand_clip_tags",
        sa.Column("hand_clip_id", sa.UUID(), nullable=False),
        sa.Column("tag_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["hand_clip_id"],
            ["pokervod.hand_clips.id"],
            name="fk_hand_clip_tags_hand_clip_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tag_id"],
            ["pokervod.tags.id"],
            name="fk_hand_clip_tags_tag_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("hand_clip_id", "tag_id"),
        schema="pokervod",
    )

    # 10. hand_clip_players (N:N)
    op.create_table(
        "hand_clip_players",
        sa.Column("hand_clip_id", sa.UUID(), nullable=False),
        sa.Column("player_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["hand_clip_id"],
            ["pokervod.hand_clips.id"],
            name="fk_hand_clip_players_hand_clip_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["player_id"],
            ["pokervod.players.id"],
            name="fk_hand_clip_players_player_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("hand_clip_id", "player_id"),
        schema="pokervod",
    )

    # 11. nas_folders
    op.create_table(
        "nas_folders",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("folder_path", sa.String(1000), nullable=False),
        sa.Column("folder_name", sa.String(500), nullable=False),
        sa.Column("parent_path", sa.String(1000), nullable=True),
        sa.Column("depth", sa.Integer(), nullable=False, default=0),
        sa.Column("file_count", sa.Integer(), nullable=False, default=0),
        sa.Column("folder_count", sa.Integer(), nullable=False, default=0),
        sa.Column("total_size_bytes", sa.BigInteger(), nullable=False, default=0),
        sa.Column("is_empty", sa.Boolean(), nullable=False, default=True),
        sa.Column("is_hidden_folder", sa.Boolean(), nullable=False, default=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_nas_folders"),
        sa.UniqueConstraint("folder_path", name="uq_nas_folders_folder_path"),
        schema="pokervod",
    )
    op.create_index("ix_nas_folders_folder_path", "nas_folders", ["folder_path"], schema="pokervod")

    # 12. nas_files
    op.create_table(
        "nas_files",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("file_path", sa.String(1000), nullable=False),
        sa.Column("file_name", sa.String(500), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=False, default=0),
        sa.Column("file_extension", sa.String(20), nullable=True),
        sa.Column("file_mtime", sa.DateTime(timezone=True), nullable=True),
        sa.Column("file_category", sa.String(20), nullable=False, default="other"),
        sa.Column("is_hidden_file", sa.Boolean(), nullable=False, default=False),
        sa.Column("video_file_id", sa.UUID(), nullable=True),
        sa.Column("folder_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_nas_files"),
        sa.UniqueConstraint("file_path", name="uq_nas_files_file_path"),
        sa.ForeignKeyConstraint(
            ["video_file_id"],
            ["pokervod.video_files.id"],
            name="fk_nas_files_video_file_id_video_files",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["folder_id"],
            ["pokervod.nas_folders.id"],
            name="fk_nas_files_folder_id_nas_folders",
            ondelete="SET NULL",
        ),
        schema="pokervod",
    )
    op.create_index("ix_nas_files_file_path", "nas_files", ["file_path"], schema="pokervod")

    # 13. google_sheet_sync
    op.create_table(
        "google_sheet_sync",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("sheet_id", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("last_row_synced", sa.Integer(), nullable=False, default=0),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sync_status", sa.String(20), nullable=False, default="idle"),
        sa.Column("error_message", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_google_sheet_sync"),
        sa.UniqueConstraint("sheet_id", "entity_type", name="uq_google_sheet_sync_sheet_entity"),
        schema="pokervod",
    )
    op.create_index("ix_google_sheet_sync_sheet_id", "google_sheet_sync", ["sheet_id"], schema="pokervod")


def downgrade() -> None:
    op.drop_table("google_sheet_sync", schema="pokervod")
    op.drop_table("nas_files", schema="pokervod")
    op.drop_table("nas_folders", schema="pokervod")
    op.drop_table("hand_clip_players", schema="pokervod")
    op.drop_table("hand_clip_tags", schema="pokervod")
    op.drop_table("hand_clips", schema="pokervod")
    op.drop_table("players", schema="pokervod")
    op.drop_table("tags", schema="pokervod")
    op.drop_table("video_files", schema="pokervod")
    op.drop_table("episodes", schema="pokervod")
    op.drop_table("events", schema="pokervod")
    op.drop_table("seasons", schema="pokervod")
    op.drop_table("projects", schema="pokervod")
    op.execute("DROP SCHEMA IF EXISTS pokervod CASCADE")
