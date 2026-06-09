import json
from pathlib import Path

from sqlmodel import Session, func, select

from app.models import Effect


def seed_effects(session: Session) -> int:
    count = session.exec(select(func.count()).select_from(Effect)).one()
    if count > 0:
        return 0

    json_path = Path(__file__).parent.parent.parent / "components_description.json"
    with open(json_path, encoding="utf-8") as f:
        entries = json.load(f)

    for entry in entries:
        session.add(Effect(
            name=entry["name"],
            category=entry["category"],
            description=entry["description"],
            library="remocn",
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
