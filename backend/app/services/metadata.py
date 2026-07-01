import random

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.niche import Niche
from app.models.title_template import TitleTemplate

_DURATION_LABEL = {
    "short": lambda s: f"{s // 60} Minutos" if s < 3600 else f"{s / 3600:.0f} Horas",
}

_TOPIC_LABELS: dict[str, str] = {
    "rain": "Lluvia Relajante",
    "ocean": "Olas del Mar",
    "garden_summer": "Jardín de Verano",
    "white_noise": "Ruido Blanco",
}

_FALLBACK_TITLES = [
    "{duration} de {label} para Dormir Bebé | Sin Cortes",
    "{duration} de {label} Continuo | Sonido para Relajarse",
    "{label} para Bebés | {duration} Sin Interrupciones",
]

_DESCRIPTIONS = {
    "white_noise": (
        "{duration} de {label_lower} en bucle continuo, pensado para ayudar a bebés "
        "(y adultos) a relajarse y conciliar el sueño. Sonido generado de forma original, "
        "sin anuncios intermedios ni cortes.\n\n"
        "✓ Ideal para siesta y noche\n"
        "✓ Bucle sin costuras\n"
        "✓ Sin anuncios en el medio\n\n"
        "#ruidoblanco #sonidosrelax #dormirbebe #{topic}"
    ),
}

_HASHTAGS = {
    "white_noise": ["ruidoblanco", "sonidosrelax", "dormirbebe", "bebes", "sueño"],
    "default": ["relax", "sonidos", "dormir"],
}


def _duration_label(seconds: int) -> str:
    if seconds >= 3600:
        h = seconds / 3600
        return f"{h:.0f} Horas" if h == int(h) else f"{h:.1f} Horas"
    return f"{seconds // 60} Minutos"


def generate_metadata(
    db: Session,
    niche_id: int,
    topic: str,
    duration_seconds: int,
    seed: int,
) -> tuple[str, str, list[str]]:
    niche: Niche | None = db.get(Niche, niche_id)
    generator_key = niche.generator_key if niche else "white_noise"

    label = _TOPIC_LABELS.get(topic, topic.replace("_", " ").title())
    duration = _duration_label(duration_seconds)

    templates = list(
        db.execute(
            select(TitleTemplate)
            .where(TitleTemplate.niche_id == niche_id)
            .order_by(TitleTemplate.score.desc())
            .limit(10)
        ).scalars().all()
    )

    rng = random.Random(seed)
    if templates:
        pattern = rng.choice(templates[:5]).template.title()
        title = f"{duration} de {pattern} | Sin Cortes"
    else:
        tmpl = rng.choice(_FALLBACK_TITLES)
        title = tmpl.format(duration=duration, label=label)

    desc_tmpl = _DESCRIPTIONS.get(generator_key, _DESCRIPTIONS["white_noise"])
    description = desc_tmpl.format(
        duration=duration,
        label=label,
        label_lower=label.lower(),
        topic=topic,
    )

    hashtags = _HASHTAGS.get(generator_key, _HASHTAGS["default"]) + [topic]
    return title, description, hashtags
