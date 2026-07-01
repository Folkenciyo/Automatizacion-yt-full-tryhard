import re
from collections import Counter

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.competitor import CompetitorChannel, CompetitorVideo
from app.models.title_template import TitleTemplate

_STOPWORDS = {
    "the", "a", "an", "and", "or", "for", "to", "of", "in", "on", "with", "is",
    "de", "la", "el", "los", "las", "un", "una", "y", "para", "con", "en",
}
_WORD_RE = re.compile(r"[a-záéíóúñü0-9]+", re.IGNORECASE)


def _tokenize(title: str) -> list[str]:
    return [w for w in _WORD_RE.findall(title.lower()) if w not in _STOPWORDS]


def compute_title_ngrams(titles: list[str], ngram_sizes: tuple[int, ...] = (1, 2, 3), top_n: int = 20) -> list[tuple[str, int]]:
    counter: Counter[str] = Counter()
    for title in titles:
        words = _tokenize(title)
        for size in ngram_sizes:
            for i in range(len(words) - size + 1):
                counter[" ".join(words[i : i + size])] += 1

    return counter.most_common(top_n)


def refresh_title_templates(db: Session, niche_id: int, top_n: int = 20) -> list[TitleTemplate]:
    titles = list(
        db.execute(
            select(CompetitorVideo.title)
            .join(CompetitorChannel, CompetitorVideo.competitor_channel_id == CompetitorChannel.id)
            .where(CompetitorChannel.niche_id == niche_id)
        )
        .scalars()
        .all()
    )

    ngrams = compute_title_ngrams(titles, top_n=top_n)

    db.execute(
        TitleTemplate.__table__.delete().where(
            TitleTemplate.niche_id == niche_id, TitleTemplate.source == "competitor_pattern"
        )
    )

    templates = [
        TitleTemplate(niche_id=niche_id, template=ngram, source="competitor_pattern", score=float(count))
        for ngram, count in ngrams
    ]
    db.add_all(templates)
    db.commit()
    return templates
