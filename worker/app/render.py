import subprocess
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from app.niches.base import NicheGenerator, RenderMetadata, RenderRequest
from app.niches.white_noise import WhiteNoiseGenerator

NICHE_REGISTRY: dict[str, NicheGenerator] = {
    "white_noise": WhiteNoiseGenerator(),
}

_FONT_SEARCH_PATHS = [
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]


@dataclass(frozen=True)
class RenderResult:
    video_path: Path
    thumbnail_path: Path
    metadata: RenderMetadata


def get_generator(generator_key: str) -> NicheGenerator:
    generator = NICHE_REGISTRY.get(generator_key)
    if generator is None:
        raise ValueError(f"no hay plugin registrado para generator_key={generator_key!r}")
    return generator


def _mux(audio_path: Path, visual_path: Path, duration_seconds: int, output_path: Path) -> None:
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-stream_loop", "-1", "-i", str(audio_path),
            "-i", str(visual_path),
            "-t", str(duration_seconds),
            "-map", "1:v", "-map", "0:a",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
            "-shortest",
            str(output_path),
        ],
        check=True,
        capture_output=True,
    )


def _strip_accents(text: str) -> str:
    """Fallback: Pillow's built-in default font has no glyphs for accented chars."""
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in _FONT_SEARCH_PATHS:
        if Path(path).exists():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default(size=size)


def _wrap_text(
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    draw: ImageDraw.ImageDraw,
    max_width: int,
) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), candidate, font=font)
        if bbox[2] - bbox[0] > max_width and current:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def _draw_sound_wave_icon(draw: ImageDraw.ImageDraw, cx: int, cy: int) -> None:
    """Draw concentric arcs opening to the right — classic sound/speaker icon."""
    for idx, radius in enumerate([22, 42, 62, 82]):
        stroke = max(3, 7 - idx * 2)
        # Arc opening to the right: from -55° to 55° (0° = 3 o'clock in Pillow)
        draw.arc(
            [cx - radius, cy - radius, cx + radius, cy + radius],
            start=-55,
            end=55,
            fill=(255, 255, 255),
            width=stroke,
        )
    # Small filled circle as the source point
    dot_r = 8
    draw.ellipse([cx - dot_r, cy - dot_r, cx + dot_r, cy + dot_r], fill=(255, 255, 255))


def _make_thumbnail(
    title: str,
    visual_path: Path,
    output_path: Path,
    mid_time_seconds: int = 10,
    width: int = 1280,
    height: int = 720,
) -> None:
    # 1. Extract mid-point frame from the rendered visual
    frame_path = output_path.parent / "_frame_tmp.jpg"
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-ss", str(mid_time_seconds),
            "-i", str(visual_path),
            "-vframes", "1",
            "-q:v", "2",
            str(frame_path),
        ],
        check=True,
        capture_output=True,
    )

    img = Image.open(frame_path).convert("RGB").resize((width, height), Image.LANCZOS)
    frame_path.unlink(missing_ok=True)

    # 2. Semi-transparent gradient overlay: lighter at top, heavier at bottom
    overlay = Image.new("RGBA", (width, height))
    ov_draw = ImageDraw.Draw(overlay)
    for y_pos in range(height):
        alpha = int(90 + 130 * (y_pos / height))
        ov_draw.line([(0, y_pos), (width, y_pos)], fill=(0, 0, 0, alpha))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

    draw = ImageDraw.Draw(img)

    # 3. Sound wave icon — top-left corner
    _draw_sound_wave_icon(draw, cx=90, cy=90)

    # 4. Title text — centered, with shadow
    font = _load_font(72)
    is_default_font = isinstance(font, ImageFont.ImageFont)
    display_title = _strip_accents(title) if is_default_font else title

    margin = 120
    lines = _wrap_text(display_title, font, draw, max_width=width - 2 * margin)

    # Estimate line height from font metrics
    sample_bbox = draw.textbbox((0, 0), "Ag", font=font)
    line_height = int((sample_bbox[3] - sample_bbox[1]) * 1.35)

    total_h = len(lines) * line_height
    y = (height - total_h) // 2 + 20  # slight downward offset

    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_w = bbox[2] - bbox[0]
        x = (width - line_w) // 2
        # Drop shadow
        draw.text((x + 3, y + 3), line, fill=(0, 0, 0), font=font)
        # Main text
        draw.text((x, y), line, fill=(255, 255, 255), font=font)
        y += line_height

    img.save(output_path, format="PNG")


def render_video(generator_key: str, request: RenderRequest) -> RenderResult:
    generator = get_generator(generator_key)
    cb = request.on_progress

    audio_path = generator.generate_audio(request)
    if cb:
        cb(10, "audio")

    visual_path = generator.generate_visual(request)
    if cb:
        cb(75, "visual")

    metadata = generator.generate_metadata(request)

    video_path = request.output_dir / "output.mp4"
    _mux(audio_path, visual_path, request.duration_seconds, video_path)
    if cb:
        cb(85, "mux")

    thumbnail_path = request.output_dir / "thumbnail.png"
    mid_time = max(5, request.duration_seconds // 2)
    _make_thumbnail(metadata.title, video_path, thumbnail_path, mid_time_seconds=mid_time)
    if cb:
        cb(95, "thumbnail")

    return RenderResult(video_path=video_path, thumbnail_path=thumbnail_path, metadata=metadata)
