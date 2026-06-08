from sqlmodel import Session, select

from app.models import Asset


def get_asset_by_id(session: Session, asset_id: str) -> Asset | None:
    return session.exec(select(Asset).where(Asset.asset_id == asset_id)).first()


def create_asset(session: Session, asset: Asset) -> Asset:
    session.add(asset)
    session.commit()
    return asset
