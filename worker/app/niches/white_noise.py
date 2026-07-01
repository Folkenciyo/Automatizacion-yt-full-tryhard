import logging
import math
import os
import re
import subprocess
import urllib.request
from pathlib import Path

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt

from app.niches.base import NicheGenerator, RenderMetadata, RenderRequest

logger = logging.getLogger(__name__)

SAMPLE_RATE = 44100
LOOP_SECONDS = 30
CROSSFADE_SECONDS = 2

# (low_hz, high_hz) bandpass per topic — shapes the noise texture.
_TOPIC_BANDS: dict[str, tuple[float, float]] = {
    "rain": (500.0, 7000.0),
    "ocean": (20.0, 800.0),
    "garden_summer": (800.0, 9000.0),
    "white_noise": (20.0, 20000.0),
    "brown_noise": (20.0, 280.0),
    "pink_noise": (20.0, 20000.0),   # shaped separately, band is a fallback
    "fan": (180.0, 5500.0),
    "womb": (25.0, 380.0),
    "heartbeat": (30.0, 180.0),
    "shower": (1200.0, 18000.0),
    "thunderstorm": (400.0, 7000.0), # base rain band; thunder overlay added separately
    "fireplace": (80.0, 3500.0),     # base warmth; crackle pops added separately
    "deep_sleep": (20.0, 4000.0),    # warm full-bass spectrum (shaped separately)
}

_TOPIC_LABELS: dict[str, str] = {
    "rain": "Lluvia Relajante",
    "ocean": "Olas del Mar",
    "garden_summer": "Jardín de Verano",
    "white_noise": "Ruido Blanco",
    "brown_noise": "Ruido Marrón",
    "pink_noise": "Ruido Rosa",
    "fan": "Ventilador",
    "womb": "Sonido de Útero",
    "heartbeat": "Latido de Corazón",
    "shower": "Ducha Relajante",
    "thunderstorm": "Tormenta con Lluvia",
    "fireplace": "Chimenea",
    "deep_sleep": "Sueño Profundo",
}

_TOPIC_COLORS: dict[str, tuple[str, str, str]] = {
    "rain": ("#0f2027", "#203a43", "#2c5364"),
    "ocean": ("#1a2980", "#26d0ce", "#1a2980"),
    "garden_summer": ("#134e5e", "#71b280", "#134e5e"),
    "white_noise": ("#2c3e50", "#4ca1af", "#2c3e50"),
    "brown_noise": ("#3e2723", "#795548", "#3e2723"),
    "pink_noise": ("#4a0030", "#880e4f", "#c2185b"),
    "fan": ("#1a237e", "#283593", "#3949ab"),
    "womb": ("#4a148c", "#6a1b9a", "#7b1fa2"),
    "heartbeat": ("#7f0000", "#c62828", "#7f0000"),
    "shower": ("#006064", "#00838f", "#006064"),
    "thunderstorm": ("#263238", "#455a64", "#37474f"),
    "fireplace": ("#bf360c", "#d84315", "#bf360c"),
    "deep_sleep": ("#020209", "#0a0a1f", "#04041a"),
}


# ---------------------------------------------------------------------------
# Low-level audio generators
# ---------------------------------------------------------------------------

def _bandpass_noise(rng: np.random.Generator, n_samples: int, band: tuple[float, float]) -> np.ndarray:
    raw = rng.standard_normal(n_samples)
    low, high = band
    high = min(high, SAMPLE_RATE / 2 - 1)
    sos = butter(4, [max(low, 1.0), high], btype="bandpass", fs=SAMPLE_RATE, output="sos")
    return sosfilt(sos, raw)


def _pink_noise_shaped(rng: np.random.Generator, n_samples: int) -> np.ndarray:
    """1/f noise: sum of octave bands with decreasing amplitude."""
    octave_bands: list[tuple[float, float, float]] = [
        (20, 40, 1.0), (40, 80, 0.9), (80, 160, 0.8),
        (160, 320, 0.7), (320, 640, 0.55), (640, 1280, 0.42),
        (1280, 2560, 0.3), (2560, 5120, 0.18), (5120, 10240, 0.08),
    ]
    result = np.zeros(n_samples)
    for low, high, weight in octave_bands:
        high = min(high, SAMPLE_RATE / 2 - 1)
        sos = butter(4, [max(low, 1.0), high], btype="bandpass", fs=SAMPLE_RATE, output="sos")
        result += weight * sosfilt(sos, rng.standard_normal(n_samples))
    return result


def _brown_noise_shaped(rng: np.random.Generator, n_samples: int) -> np.ndarray:
    """1/f² noise: integrate white noise then low-pass filter."""
    raw = rng.standard_normal(n_samples)
    integrated = np.cumsum(raw)
    integrated -= integrated.mean()
    sos = butter(6, 280.0, btype="low", fs=SAMPLE_RATE, output="sos")
    return sosfilt(sos, integrated)


def _deep_sleep_noise(rng: np.random.Generator, n_samples: int) -> np.ndarray:
    """60% brown + 40% pink, gentle low-pass to remove any harsh highs."""
    brown = _brown_noise_shaped(rng, n_samples)
    pink = _pink_noise_shaped(rng, n_samples)
    mixed = 0.6 * brown + 0.4 * pink
    sos = butter(4, 4000.0, btype="low", fs=SAMPLE_RATE, output="sos")
    return sosfilt(sos, mixed)


# ---------------------------------------------------------------------------
# Seamless loop helpers
# ---------------------------------------------------------------------------

def _seamless_crossfade(signal: np.ndarray, crossfade_samples: int) -> np.ndarray:
    body_len = len(signal) - crossfade_samples
    head = signal[:crossfade_samples]
    tail = signal[body_len:]
    fade_out = np.linspace(1.0, 0.0, crossfade_samples)
    fade_in = np.linspace(0.0, 1.0, crossfade_samples)
    blended_tail = tail * fade_out + head * fade_in
    return np.concatenate([signal[:body_len], blended_tail])


def _tileable_intensity_envelope(n_samples: int, loop_seconds: float, seed: int) -> np.ndarray:
    """Sum of sines whose periods divide the loop length exactly, so it tiles with no seam."""
    t = np.linspace(0, loop_seconds, n_samples, endpoint=False)
    rng = np.random.default_rng(seed)
    envelope = np.ones(n_samples)
    for harmonic in (1, 2, 3):
        amplitude = rng.uniform(0.03, 0.08) / harmonic
        phase = rng.uniform(0, 2 * np.pi)
        envelope += amplitude * np.sin(2 * np.pi * harmonic * t / loop_seconds + phase)
    return np.clip(envelope, 0.5, 1.2)


# ---------------------------------------------------------------------------
# Topic-specific modulation overlays
# ---------------------------------------------------------------------------

def _heartbeat_envelope(n_samples: int, seed: int) -> np.ndarray:
    """LUB-DUB pattern at exactly 60 BPM — tiles perfectly in a 30 s loop."""
    beat_period = SAMPLE_RATE  # 60 BPM = 1 beat/s = 44100 samples
    envelope = np.ones(n_samples) * 0.05
    beat = 0
    while beat * beat_period < n_samples:
        pos = int(beat * beat_period)
        lub_len = int(SAMPLE_RATE * 0.14)
        end = min(pos + lub_len, n_samples)
        if end > pos:
            t = np.arange(end - pos)
            envelope[pos:end] += np.exp(-t / (SAMPLE_RATE * 0.035)) * 1.8
        dub_pos = pos + int(SAMPLE_RATE * 0.22)
        if dub_pos < n_samples:
            end = min(dub_pos + lub_len, n_samples)
            t = np.arange(end - dub_pos)
            envelope[dub_pos:end] += np.exp(-t / (SAMPLE_RATE * 0.025)) * 1.1
        beat += 1
    return np.clip(envelope, 0.0, 2.5)


def _fan_envelope(n_samples: int, loop_seconds: float) -> np.ndarray:
    """Subtle blade-frequency modulation at ~12 Hz for that electric-fan texture."""
    t = np.linspace(0, loop_seconds, n_samples, endpoint=False)
    envelope = np.ones(n_samples)
    envelope += 0.07 * np.sin(2 * np.pi * 12.0 * t)
    envelope += 0.03 * np.sin(2 * np.pi * 24.0 * t)
    return np.clip(envelope, 0.7, 1.3)


def _add_thunder_rumbles(rng: np.random.Generator, base: np.ndarray, n_samples: int) -> np.ndarray:
    """Overlay 2-4 low-frequency thunder bursts within the 30 s body."""
    result = base.copy()
    n_thunders = int(rng.integers(2, 5))
    for _ in range(n_thunders):
        t_pos = int(rng.uniform(1.5, LOOP_SECONDS - 3.0) * SAMPLE_RATE)
        rumble_len = int(SAMPLE_RATE * rng.uniform(1.2, 2.5))
        end = min(t_pos + rumble_len, n_samples)
        if end <= t_pos:
            continue
        raw = rng.standard_normal(end - t_pos)
        sos = butter(4, [20.0, 180.0], btype="bandpass", fs=SAMPLE_RATE, output="sos")
        rumble = sosfilt(sos, raw)
        env_len = end - t_pos
        env = np.exp(-np.arange(env_len) / (SAMPLE_RATE * 0.45)) * rng.uniform(0.6, 1.2)
        result[t_pos:end] += rumble * env
    return result


def _add_fireplace_crackles(rng: np.random.Generator, base: np.ndarray, n_samples: int) -> np.ndarray:
    """Scatter 40-90 high-frequency crackle pops over the base signal."""
    result = base.copy()
    n_crackles = int(rng.integers(40, 90))
    sos = butter(4, 2000.0, btype="high", fs=SAMPLE_RATE, output="sos")
    for _ in range(n_crackles):
        max_pos = max(1, n_samples - SAMPLE_RATE // 8)
        pos = int(rng.integers(0, max_pos))
        crackle_len = int(rng.integers(SAMPLE_RATE // 120, SAMPLE_RATE // 30))
        end = min(pos + crackle_len, n_samples)
        if end <= pos:
            continue
        raw = rng.standard_normal(end - pos)
        crackle = sosfilt(sos, raw)
        amplitude = rng.uniform(0.4, 1.4)
        env = np.exp(-np.arange(end - pos) / (SAMPLE_RATE * 0.004)) * amplitude
        result[pos:end] += crackle * env
    return result


# ---------------------------------------------------------------------------
# Per-topic audio dispatch
# ---------------------------------------------------------------------------

def _generate_single_audio(
    topic: str, rng: np.random.Generator, n_samples: int, seed: int
) -> np.ndarray:
    if topic == "pink_noise":
        noise = _pink_noise_shaped(rng, n_samples)
    elif topic == "brown_noise":
        noise = _brown_noise_shaped(rng, n_samples)
    elif topic == "deep_sleep":
        noise = _deep_sleep_noise(rng, n_samples)
    else:
        band = _TOPIC_BANDS.get(topic, _TOPIC_BANDS["white_noise"])
        noise = _bandpass_noise(rng, n_samples, band)

    if topic in ("heartbeat", "womb"):
        noise = noise * _heartbeat_envelope(n_samples, seed)
    elif topic == "fan":
        noise = noise * _fan_envelope(n_samples, float(LOOP_SECONDS))
    elif topic == "thunderstorm":
        noise = _add_thunder_rumbles(rng, noise, n_samples)
    elif topic == "fireplace":
        noise = _add_fireplace_crackles(rng, noise, n_samples)

    return noise


# ---------------------------------------------------------------------------
# Mix topic parser
# ---------------------------------------------------------------------------

def _parse_mix_topic(topic: str) -> tuple[str, str | None, float]:
    """
    "rain"            → ("rain", None, 1.0)
    "rain+ocean"      → ("rain", "ocean", 0.5)
    "rain+ocean:0.7"  → ("rain", "ocean", 0.7) — 70 % rain, 30 % ocean
    """
    if "+" not in topic:
        return topic, None, 1.0
    t1, rest = topic.split("+", 1)
    if ":" in rest:
        t2, balance_str = rest.split(":", 1)
        try:
            balance = float(balance_str)
        except ValueError:
            balance = 0.5
    else:
        t2, balance = rest, 0.5
    return t1.strip(), t2.strip(), float(np.clip(balance, 0.1, 0.9))


# ---------------------------------------------------------------------------
# Visual generation — helpers
# ---------------------------------------------------------------------------

_GEQ_LOOP_SECONDS = 60  # procedural clips are 60 s; mux loops them to full duration

_AI_PROMPTS: dict[str, str] = {
    "rain":         "Gentle rain falling on dark water at night, macro slow motion, cinematic 4K, dark moody atmosphere, no text no watermark",
    "ocean":        "Dark ocean waves rolling slowly at moonrise, aerial view, cinematic 4K, deep blue tones, no text no watermark",
    "garden_summer":"Lush dark forest at night with fireflies and wind in leaves, cinematic 4K, moody greens, no text no watermark",
    "white_noise":  "Abstract dark smoke swirling slowly, black background, silver and white tones, cinematic 4K, no text no watermark",
    "brown_noise":  "Warm amber fog slowly drifting in darkness, deep brown and gold tones, cinematic 4K, no text no watermark",
    "pink_noise":   "Soft pink and purple light gently pulsing in darkness, abstract, cinematic 4K, no text no watermark",
    "fan":          "Electric fan blades spinning in a dark room with blue light, close-up, cinematic 4K, no text no watermark",
    "womb":         "Warm amber organic fluid shapes slowly pulsing, dark reddish background, abstract cinematic 4K, no text no watermark",
    "heartbeat":    "Abstract deep crimson light slowly pulsing, organic shapes in darkness, cinematic 4K, no text no watermark",
    "shower":       "Water droplets falling on dark glass in slow motion, blue-grey tones, macro close-up, cinematic 4K, no text no watermark",
    "thunderstorm": "Dark storm clouds with distant lightning flashes, dramatic sky, cinematic 4K, no text no watermark",
    "fireplace":    "Crackling fireplace flames close-up, orange and amber tones, dark background, cinematic 4K, no text no watermark",
    "deep_sleep":   "Deep cosmic nebula slowly swirling, midnight blue and deep purple, cinematic 4K, no text no watermark",
}
_AI_DEFAULT_PROMPT = "Abstract dark fluid motion, slowly shifting deep colors, relaxing ambient, cinematic 4K, no text no watermark"


def _run_ffmpeg_encode(
    lavfi: str,
    output_path: Path,
    progress_cb: "Callable[[int], None] | None" = None,
    clip_duration: float = 60.0,
) -> None:
    args = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", lavfi,
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast",
        str(output_path),
    ]
    if progress_cb is None:
        subprocess.run(args, check=True, capture_output=True)
        return

    time_re = re.compile(r"time=(\d+):(\d+):(\d+\.?\d*)")
    proc = subprocess.Popen(args, stderr=subprocess.PIPE, stdout=subprocess.DEVNULL, text=True)
    assert proc.stderr is not None
    for line in proc.stderr:
        m = time_re.search(line)
        if m:
            elapsed = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
            progress_cb(min(99, int(elapsed / clip_duration * 100)))
    proc.wait()
    if proc.returncode != 0:
        raise subprocess.CalledProcessError(proc.returncode, args)


def _visual_gradient(request: RenderRequest) -> Path:
    topic1, topic2, _balance = _parse_mix_topic(request.topic)
    c1 = _TOPIC_COLORS.get(topic1, _TOPIC_COLORS["white_noise"])
    if topic2 is not None:
        c2 = _TOPIC_COLORS.get(topic2, _TOPIC_COLORS["white_noise"])
        colors = (c1[0], c2[1], c1[2])
    else:
        colors = c1

    output_path = request.output_dir / "visual.mp4"
    request.output_dir.mkdir(parents=True, exist_ok=True)
    lavfi = (
        f"gradients=size={request.width}x{request.height}"
        f":duration={request.duration_seconds}"
        f":seed={request.seed}:speed=0.015:type=2:n=3"
        f":c0={colors[0]}:c1={colors[1]}:c2={colors[2]}"
    )
    _run_ffmpeg_encode(lavfi, output_path)
    return output_path


def _geq_visual(request: RenderRequest, bg_color: str, geq_expr: str) -> Path:
    """Generate a GEQ-based 60 s clip and loop it to the full render duration."""
    W, H = request.width, request.height
    request.output_dir.mkdir(parents=True, exist_ok=True)
    short_path = request.output_dir / "_geq_clip.mp4"
    output_path = request.output_dir / "visual.mp4"
    lavfi = (
        f"color=c={bg_color}:size={W}x{H}:duration={_GEQ_LOOP_SECONDS}:rate=24,"
        f"format=gbrp,geq={geq_expr}"
    )
    cb = request.on_progress
    _run_ffmpeg_encode(
        lavfi, short_path,
        progress_cb=(lambda pct: cb(10 + int(pct * 0.65), "visual")) if cb else None,
        clip_duration=float(_GEQ_LOOP_SECONDS),
    )
    _loop_clip_to_duration(short_path, request.duration_seconds, output_path)
    short_path.unlink(missing_ok=True)
    return output_path


def _visual_plasma(request: RenderRequest) -> Path:
    """Psychedelic plasma — three sinusoidal color waves at different frequencies."""
    return _geq_visual(
        request,
        bg_color="#000010",
        geq_expr=(
            "r='128+100*sin(0.025*X+T*0.8)+28*sin(0.015*Y-T*0.6)':"
            "g='128+80*sin(0.02*Y+T*0.7+1)+48*sin(0.018*X-T*0.5)':"
            "b='200+55*sin(0.012*(X+Y)-T*0.9)'"
        ),
    )


def _visual_waves(request: RenderRequest) -> Path:
    """Rippling ocean-like horizontal waves — blue-green palette."""
    return _geq_visual(
        request,
        bg_color="#000020",
        geq_expr=(
            "r='20+15*abs(sin(0.04*X-T*0.5))*abs(cos(0.02*Y+T*0.15))':"
            "g='80+70*abs(sin(0.035*X-T*0.45+0.5))*abs(sin(0.025*Y+T*0.2))':"
            "b='160+95*abs(sin(0.03*X-T*0.4))*abs(cos(0.018*Y-T*0.12))'"
        ),
    )


def _visual_aurora(request: RenderRequest) -> Path:
    """Northern-lights bands — green dominant, slow horizontal wave drift."""
    return _geq_visual(
        request,
        bg_color="#000205",
        geq_expr=(
            "r='70*pow(max(0,sin(0.008*Y+0.3*sin(0.003*X+T*0.1)+T*0.07)),3)':"
            "g='200*pow(max(0,sin(0.006*Y+0.4*sin(0.004*X+T*0.08)+T*0.055)),2)':"
            "b='130*pow(max(0,sin(0.007*Y+0.2*sin(0.005*X+T*0.09)+T*0.048)),2)'"
        ),
    )


def _clip_duration_seconds(path: Path) -> int:
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True,
    )
    try:
        return max(3, int(float(result.stdout.strip())))
    except (ValueError, AttributeError):
        return 30


def _loop_clip_to_duration(short_path: Path, duration_seconds: int, output_path: Path) -> None:
    clip_dur = _clip_duration_seconds(short_path)
    n = math.ceil(duration_seconds / clip_dur) + 1
    list_path = output_path.parent / "_concat.txt"
    list_path.write_text("\n".join(f"file '{short_path}'" for _ in range(n)))
    subprocess.run(
        ["ffmpeg", "-y",
         "-f", "concat", "-safe", "0", "-i", str(list_path),
         "-t", str(duration_seconds),
         "-c:v", "copy",
         str(output_path)],
        check=True, capture_output=True,
    )
    list_path.unlink(missing_ok=True)


_HF_VIDEO_MODELS = [
    "cerspense/zeroscope_v2_576w",
    "ali-vilab/text-to-video-ms-1.7b",
]


def _visual_ai(request: RenderRequest) -> Path:
    """Generate a short AI video via HuggingFace (hf-inference provider) and loop it.
    Tries each model in _HF_VIDEO_MODELS in order; falls back to gradient if all fail.
    """
    hf_token = os.environ.get("HF_TOKEN")
    if not hf_token:
        logger.warning("HF_TOKEN not set — falling back to gradient visual")
        return _visual_gradient(request)

    try:
        from huggingface_hub import InferenceClient  # type: ignore[import-untyped]
    except ImportError:
        logger.error("huggingface_hub not installed — falling back to gradient")
        return _visual_gradient(request)

    topic1 = request.topic.split("+")[0]
    prompt = _AI_PROMPTS.get(topic1, _AI_DEFAULT_PROMPT)

    for model_id in _HF_VIDEO_MODELS:
        logger.info("Trying HuggingFace model %s via hf-inference", model_id)
        try:
            client = InferenceClient(token=hf_token, provider="hf-inference")
            video_bytes = client.text_to_video(prompt, model=model_id)

            request.output_dir.mkdir(parents=True, exist_ok=True)
            short_path = request.output_dir / "_ai_clip.mp4"
            short_path.write_bytes(video_bytes)

            encoded_path = request.output_dir / "_ai_encoded.mp4"
            subprocess.run(
                ["ffmpeg", "-y", "-i", str(short_path),
                 "-vf", (
                     f"scale={request.width}:{request.height}"
                     f":force_original_aspect_ratio=decrease,"
                     f"pad={request.width}:{request.height}:(ow-iw)/2:(oh-ih)/2"
                 ),
                 "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast",
                 str(encoded_path)],
                check=True, capture_output=True,
            )
            short_path.unlink(missing_ok=True)

            output_path = request.output_dir / "visual.mp4"
            _loop_clip_to_duration(encoded_path, request.duration_seconds, output_path)
            encoded_path.unlink(missing_ok=True)
            logger.info("AI visual generated with %s", model_id)
            return output_path

        except Exception as exc:
            logger.warning("Model %s failed: %s", model_id, exc)
            continue

    logger.error("All HuggingFace models failed — falling back to gradient")
    return _visual_gradient(request)


_VISUAL_DISPATCH: dict[str, object] = {
    "gradient": _visual_gradient,
    "plasma":   _visual_plasma,
    "waves":    _visual_waves,
    "aurora":   _visual_aurora,
    "ai":       _visual_ai,
}


# ---------------------------------------------------------------------------
# Plugin class
# ---------------------------------------------------------------------------

class WhiteNoiseGenerator(NicheGenerator):
    def generate_audio(self, request: RenderRequest) -> Path:
        topic1, topic2, balance = _parse_mix_topic(request.topic)
        rng = np.random.default_rng(request.seed)

        crossfade_samples = CROSSFADE_SECONDS * SAMPLE_RATE
        total_samples = LOOP_SECONDS * SAMPLE_RATE + crossfade_samples

        noise = _generate_single_audio(topic1, rng, total_samples, request.seed)

        if topic2 is not None:
            rng2 = np.random.default_rng(request.seed + 1)
            noise2 = _generate_single_audio(topic2, rng2, total_samples, request.seed + 1)
            noise = balance * noise + (1 - balance) * noise2

        looped = _seamless_crossfade(noise, crossfade_samples)
        envelope = _tileable_intensity_envelope(len(looped), LOOP_SECONDS, request.seed)
        shaped = looped * envelope
        shaped = shaped / (np.max(np.abs(shaped)) + 1e-9) * 0.9
        pcm = (shaped * np.iinfo(np.int16).max).astype(np.int16)

        output_path = request.output_dir / "audio_loop.wav"
        request.output_dir.mkdir(parents=True, exist_ok=True)
        wavfile.write(output_path, SAMPLE_RATE, pcm)
        return output_path

    def generate_visual(self, request: RenderRequest) -> Path:
        fn = _VISUAL_DISPATCH.get(request.visual_style, _visual_gradient)
        return fn(request)  # type: ignore[operator]

    def generate_metadata(self, request: RenderRequest) -> RenderMetadata:
        topic1, topic2, _balance = _parse_mix_topic(request.topic)
        label1 = _TOPIC_LABELS.get(topic1, topic1.replace("_", " ").title())

        if topic2 is not None:
            label2 = _TOPIC_LABELS.get(topic2, topic2.replace("_", " ").title())
            label = f"{label1} + {label2}"
        else:
            label = label1

        hours = request.duration_seconds / 3600
        minutes = request.duration_seconds / 60
        if hours >= 1:
            duration_label = f"{hours:.1f} Horas"
        elif minutes >= 1:
            duration_label = f"{minutes:.0f} Minutos"
        else:
            duration_label = f"{request.duration_seconds} Segundos"

        title = f"{duration_label} de {label} para Dormir Bebé | Sin Cortes"
        description = (
            f"{duration_label} de {label.lower()} en bucle continuo, pensado para ayudar a bebés "
            "(y adultos) a relajarse y dormir mejor. Sonido y visual generados de forma original, "
            "sin anuncios intermedios.\n\n"
            "#ruidoblanco #sonidosrelax #dormirbebe"
        )
        hashtags = ["ruidoblanco", "sonidosrelax", "dormirbebe", topic1]
        if topic2:
            hashtags.append(topic2)
        return RenderMetadata(title=title, description=description, hashtags=hashtags)
