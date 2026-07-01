import argparse
import logging
import sys
from pathlib import Path

from app.niches.base import RenderRequest
from app.render import render_video

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("cli")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Renderiza un video de prueba end-to-end (audio + visual + mux)")
    parser.add_argument("--generator", default="white_noise", help="generator_key del nicho (ver render.NICHE_REGISTRY)")
    parser.add_argument("--topic", default="rain", help="rain | ocean | garden_summer | white_noise")
    parser.add_argument("--duration", type=int, default=60, help="duración en segundos")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--output-dir", type=Path, default=Path("output"))

    args = parser.parse_args(argv)

    request = RenderRequest(
        topic=args.topic,
        duration_seconds=args.duration,
        seed=args.seed,
        output_dir=args.output_dir,
    )

    logger.info("renderizando topic=%s duration=%ss seed=%s -> %s", args.topic, args.duration, args.seed, args.output_dir)
    result = render_video(args.generator, request)

    logger.info("video: %s", result.video_path)
    logger.info("thumbnail: %s", result.thumbnail_path)
    logger.info("titulo: %s", result.metadata.title)
    return 0


if __name__ == "__main__":
    sys.exit(main())
