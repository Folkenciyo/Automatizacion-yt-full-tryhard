"""add studio models: video_clips, audio_assets, storyboards, story_prompts

Revision ID: a3f9b2c1d4e5
Revises: 260173816f1b
Create Date: 2026-06-30

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a3f9b2c1d4e5"
down_revision: Union[str, Sequence[str], None] = "260173816f1b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "video_clips",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("queued", "generating", "ready", "failed", name="videoclipstatus"),
            nullable=False,
            server_default="queued",
        ),
        sa.Column("num_frames", sa.Integer(), nullable=False, server_default="24"),
        sa.Column("duration_seconds", sa.Float(), nullable=False, server_default="3.0"),
        sa.Column("render_server_job_id", sa.String(64), nullable=True),
        sa.Column("file_path", sa.String(512), nullable=True),
        sa.Column("thumbnail_path", sa.String(512), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "audio_assets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("source", sa.String(32), nullable=False, server_default="import"),
        sa.Column("file_path", sa.String(512), nullable=False),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "storyboards",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("channel_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("story_text", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("draft", "generating", "ready", name="storyboardstatus"),
            nullable=False,
            server_default="draft",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["channel_id"], ["channels.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "story_prompts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("storyboard_id", sa.Integer(), nullable=False),
        sa.Column("clip_id", sa.Integer(), nullable=True),
        sa.Column("order", sa.Integer(), nullable=False),
        sa.Column("prompt_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["storyboard_id"], ["storyboards.id"]),
        sa.ForeignKeyConstraint(["clip_id"], ["video_clips.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("story_prompts")
    op.drop_table("storyboards")
    op.drop_table("audio_assets")
    op.drop_table("video_clips")
    op.execute("DROP TYPE IF EXISTS videoclipstatus")
    op.execute("DROP TYPE IF EXISTS storyboardstatus")
