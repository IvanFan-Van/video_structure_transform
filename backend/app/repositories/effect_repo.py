import json
import re
from pathlib import Path

from sqlmodel import Session, func, select

from app.models import Effect

REPO_ROOT = Path(__file__).parent.parent.parent.parent
OUT_DIR = REPO_ROOT / "effects-renderer" / "out"


def _pascal_to_kebab(name: str) -> str:
    return re.sub(
        r"(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])",
        "-",
        name,
    ).lower()


def seed_effects(session: Session) -> int:
    count = session.exec(select(func.count()).select_from(Effect)).one()
    if count > 0:
        return 0

    json_path = REPO_ROOT / "backend" / "components_description.json"
    with open(json_path, encoding="utf-8") as f:
        entries = json.load(f)

    for entry in entries:
        kebab = _pascal_to_kebab(entry["name"])
        demo_file = OUT_DIR / f"{kebab}.mp4"
        demo_path = f"/effects/demo/{kebab}.mp4" if demo_file.exists() else None
        session.add(Effect(
            name=entry["name"],
            category=entry["category"],
            description=entry["description"],
            library="remocn",
            demo_path=demo_path,
        ))
    session.commit()
    return len(entries)


def search_effects(session: Session, q: str | None) -> list[Effect]:
    if not q:
        return list(session.exec(select(Effect)).all())
    pattern = f"%{q}%"
    return list(session.exec(
        select(Effect).where(
            Effect.name.ilike(pattern)
            | Effect.description.ilike(pattern)
            | Effect.category.ilike(pattern)
        )
    ).all())
