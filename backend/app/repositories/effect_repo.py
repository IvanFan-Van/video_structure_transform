import json
import logging
import re

from sqlmodel import Session, func, select

from app.config import COMPONENTS_JSON, EFFECT_DIR, EFFECT_DOC_DIR
from app.models import Effect

logger = logging.getLogger(__name__)


def _pascal_to_kebab(name: str) -> str:
    return re.sub(
        r"(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])",
        "-",
        name,
    ).lower()


def seed_effects(session: Session) -> int:
    logger.info("Checking effects seed status...")

    count = session.exec(select(func.count()).select_from(Effect)).one()
    if count > 0:
        logger.info("Effects already seeded (%d rows), skipping.", count)
        return 0

    logger.info("Loading effects from %s", COMPONENTS_JSON)
    with open(COMPONENTS_JSON, encoding="utf-8") as f:
        entries = json.load(f)

    logger.info("Loaded %d effect entries, seeding...", len(entries))

    demo_found = 0
    doc_found = 0
    for entry in entries:
        kebab = _pascal_to_kebab(entry["name"])
        demo_file = EFFECT_DIR / f"{kebab}.mp4"
        doc_file = EFFECT_DOC_DIR / f"{kebab}.md"
        demo_path = f"/effects/demo/{kebab}.mp4" if demo_file.exists() else None
        doc_path = f"/effects/doc/{kebab}.md" if doc_file.exists() else None
        if demo_path:
            demo_found += 1
        else:
            logger.warning(
                "Demo video not found for effect '%s' (expected at %s)",
                entry["name"],
                demo_file,
            )
        if doc_path:
            doc_found += 1
        else:
            logger.warning(
                "Doc file not found for effect '%s' (expected at %s)",
                entry["name"],
                doc_file,
            )
        session.add(
            Effect(
                name=entry["name"],
                category=entry["category"],
                description=entry["description"],
                library="remocn",
                demo_path=demo_path,
                doc_path=doc_path,
            )
        )
    session.commit()
    logger.info(
        "Seeded %d effects (%d with demo videos, %d with docs).",
        len(entries),
        demo_found,
        doc_found,
    )
    return len(entries)


def search_effects(session: Session, q: str | None) -> list[Effect]:
    if not q:
        return list(session.exec(select(Effect)).all())
    pattern = f"%{q}%"
    return list(
        session.exec(
            select(Effect).where(
                Effect.name.ilike(pattern)  # type: ignore
                | Effect.description.ilike(pattern)  # type: ignore
                | Effect.category.ilike(pattern)  # type: ignore
            )
        ).all()
    )
