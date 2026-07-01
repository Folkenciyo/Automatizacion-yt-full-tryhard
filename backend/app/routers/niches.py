from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.niche import Niche
from app.schemas import NicheCreate, NicheRead

router = APIRouter(prefix="/niches", tags=["niches"])


@router.get("", response_model=list[NicheRead])
def list_niches(db: Session = Depends(get_db)) -> list[Niche]:
    return list(db.execute(select(Niche)).scalars().all())


@router.post("", response_model=NicheRead, status_code=201)
def create_niche(payload: NicheCreate, db: Session = Depends(get_db)) -> Niche:
    existing = db.execute(select(Niche).where(Niche.slug == payload.slug)).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=409, detail=f"niche '{payload.slug}' already exists")

    niche = Niche(**payload.model_dump())
    db.add(niche)
    db.commit()
    db.refresh(niche)
    return niche
