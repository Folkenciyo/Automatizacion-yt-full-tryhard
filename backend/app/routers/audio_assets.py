from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.models.audio_asset import AudioAsset
from app.schemas import AudioAssetRead

router = APIRouter(prefix="/audio-assets", tags=["audio"])

AUDIO_DIR = Path(settings.render_output_dir) / "audio"


@router.get("", response_model=list[AudioAssetRead])
def list_audio(db: Session = Depends(get_db)):
    return db.query(AudioAsset).order_by(AudioAsset.created_at.desc()).all()


@router.post("", response_model=AudioAssetRead)
async def upload_audio(
    title: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    ext = Path(file.filename or "audio.mp3").suffix or ".mp3"
    asset = AudioAsset(title=title, source="import")
    db.add(asset)
    db.flush()

    dest = AUDIO_DIR / f"audio_{asset.id}{ext}"
    dest.write_bytes(await file.read())
    asset.file_path = str(dest)

    try:
        import subprocess
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(dest)],
            capture_output=True, text=True, timeout=10,
        )
        asset.duration_seconds = float(result.stdout.strip())
    except Exception:
        pass

    db.commit()
    db.refresh(asset)
    return asset


@router.get("/{asset_id}", response_model=AudioAssetRead)
def get_audio(asset_id: int, db: Session = Depends(get_db)):
    asset = db.get(AudioAsset, asset_id)
    if not asset:
        raise HTTPException(404, "Audio not found")
    return asset


@router.delete("/{asset_id}")
def delete_audio(asset_id: int, db: Session = Depends(get_db)):
    asset = db.get(AudioAsset, asset_id)
    if not asset:
        raise HTTPException(404, "Audio not found")
    try:
        Path(asset.file_path).unlink(missing_ok=True)
    except Exception:
        pass
    db.delete(asset)
    db.commit()
    return {"ok": True}
