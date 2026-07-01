from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class RenderRequest:
    topic: str
    duration_seconds: int
    seed: int
    output_dir: Path
    width: int = 1920
    height: int = 1080
    visual_style: str = "gradient"
    on_progress: Callable[[int, str], None] | None = field(default=None, compare=False, repr=False)


@dataclass(frozen=True)
class RenderMetadata:
    title: str
    description: str
    hashtags: list[str]


class NicheGenerator(ABC):
    """Common interface every niche plugin implements.

    The render pipeline (app/render.py) only depends on this interface, so a
    new niche (e.g. kids_songs) plugs in without touching the orchestration.
    """

    @abstractmethod
    def generate_audio(self, request: RenderRequest) -> Path:
        """Return the path to a short, seamlessly-loopable audio file."""

    @abstractmethod
    def generate_visual(self, request: RenderRequest) -> Path:
        """Return the path to the full-duration background video (no audio)."""

    @abstractmethod
    def generate_metadata(self, request: RenderRequest) -> RenderMetadata:
        """Return title/description/hashtags for the rendered video."""
