from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.channel import ChannelStatus
from app.models.storyboard import StoryboardStatus
from app.models.video_clip import VideoClipStatus
from app.models.video_project import VideoProjectStatus


class NicheCreate(BaseModel):
    slug: str
    name: str
    generator_key: str
    made_for_kids_default: bool = False


class NicheRead(NicheCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class ChannelCreate(BaseModel):
    niche_id: int
    display_name: str
    youtube_channel_id: str | None = None
    oauth_credentials_ref: str | None = None


class ChannelRead(ChannelCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: ChannelStatus
    created_at: datetime


class CompetitorChannelIngest(BaseModel):
    niche_id: int
    youtube_channel_id: str
    max_videos: int = 25


class CompetitorVideoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    youtube_video_id: str
    title: str
    published_at: datetime | None
    duration_seconds: int
    view_count: int
    like_count: int
    comment_count: int
    thumbnail_url: str | None


class CompetitorChannelRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    niche_id: int
    youtube_channel_id: str
    title: str
    description: str | None
    subscriber_count: int
    view_count: int
    video_count: int
    fetched_at: datetime


class TitleTemplateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    niche_id: int
    template: str
    source: str
    score: float | None


class VideoProjectCreate(BaseModel):
    topic: str
    duration_seconds: int = 3600
    seed: int = 0
    visual_style: str = "gradient"


class RenderRequest(BaseModel):
    topic: str
    duration_seconds: int = 3600
    seed: int = 0
    visual_style: str = "gradient"


class VideoProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    channel_id: int
    status: VideoProjectStatus
    title: str | None
    description: str | None
    hashtags: str | None
    render_output_path: str | None
    youtube_video_id: str | None
    scheduled_at: datetime | None
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime


# --- VideoClip ---

class VideoClipCreate(BaseModel):
    prompt: str
    num_frames: int = 24
    num_steps: int = 10
    width: int = 512
    height: int = 288


class VideoClipRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    prompt: str
    status: VideoClipStatus
    num_frames: int
    duration_seconds: float
    render_server_job_id: Optional[str]
    file_path: Optional[str]
    thumbnail_path: Optional[str]
    error: Optional[str]
    created_at: datetime
    updated_at: datetime
    storyboard_id: Optional[int] = None
    storyboard_title: Optional[str] = None
    storyboard_story_text: Optional[str] = None


# --- AudioAsset ---

class AudioAssetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    source: str
    file_path: str
    duration_seconds: Optional[float]
    created_at: datetime


# --- Storyboard ---

class StoryPromptCreate(BaseModel):
    prompt_text: str
    order: int


class StoryPromptUpdate(BaseModel):
    prompt_text: str


class StoryPromptRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order: int
    prompt_text: str
    clip_id: Optional[int]
    clip: Optional[VideoClipRead]
    created_at: datetime


class StoryboardCreate(BaseModel):
    channel_id: int
    title: str
    story_text: str
    prompts: list[StoryPromptCreate]


class StoryboardRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    channel_id: int
    title: str
    story_text: str
    status: StoryboardStatus
    prompts: list[StoryPromptRead]
    created_at: datetime
    updated_at: datetime
