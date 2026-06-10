import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

import config
from ai_analyzer import analyze_photo
from cloud_sync import S3Syncer
from database import get_db, init_db
from exif_parser import extract_exif, generate_thumbnail, is_supported
from models import (
    AnalyzeRequest,
    PhotoDB,
    PhotoOut,
    ScanRequest,
    SettingsUpdate,
    SyncRequest,
)

app = FastAPI(title="Photo Manager API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

Path(config.load()["thumbnail_dir"]).mkdir(parents=True, exist_ok=True)


# ── Photos ──────────────────────────────────────────────────────────────────

@app.get("/api/photos", response_model=list[PhotoOut])
def list_photos(
    theme: Optional[str] = Query(None),
    camera_model: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    db: Session = Depends(get_db),
):
    q = db.query(PhotoDB)

    if theme:
        q = q.filter(PhotoDB.ai_theme.ilike(f"%{theme}%"))
    if camera_model:
        q = q.filter(PhotoDB.camera_model.ilike(f"%{camera_model}%"))
    if date_from:
        q = q.filter(PhotoDB.shot_at >= datetime.fromisoformat(date_from))
    if date_to:
        q = q.filter(PhotoDB.shot_at <= datetime.fromisoformat(date_to))
    if search:
        like = f"%{search}%"
        q = q.filter(
            PhotoDB.ai_description.ilike(like)
            | PhotoDB.ai_tags.ilike(like)
            | PhotoDB.ai_theme.ilike(like)
            | PhotoDB.file_name.ilike(like)
        )

    return q.order_by(PhotoDB.shot_at.desc()).offset(offset).limit(limit).all()


@app.get("/api/photos/{photo_id}", response_model=PhotoOut)
def get_photo(photo_id: int, db: Session = Depends(get_db)):
    photo = db.get(PhotoDB, photo_id)
    if not photo:
        raise HTTPException(404, "Photo not found")
    return photo


@app.get("/api/photos/{photo_id}/image")
def serve_image(photo_id: int, db: Session = Depends(get_db)):
    photo = db.get(PhotoDB, photo_id)
    if not photo or not Path(photo.file_path).exists():
        raise HTTPException(404, "Image file not found")
    return FileResponse(photo.file_path)


@app.get("/api/photos/{photo_id}/thumbnail")
def serve_thumbnail(photo_id: int, db: Session = Depends(get_db)):
    photo = db.get(PhotoDB, photo_id)
    if not photo:
        raise HTTPException(404)
    if photo.thumbnail_path and Path(photo.thumbnail_path).exists():
        return FileResponse(photo.thumbnail_path)
    if Path(photo.file_path).exists():
        return FileResponse(photo.file_path)
    raise HTTPException(404, "Image not found")


# ── Scan directory ───────────────────────────────────────────────────────────

@app.post("/api/scan")
def scan_directory(req: ScanRequest, db: Session = Depends(get_db)):
    base = Path(req.directory)
    if not base.exists():
        raise HTTPException(400, f"Directory does not exist: {req.directory}")

    cfg = config.load()
    thumb_dir = Path(cfg["thumbnail_dir"])
    thumb_size = cfg["thumbnail_size"]

    pattern = "**/*" if req.recursive else "*"
    added, skipped = 0, 0

    for file_path in base.glob(pattern):
        if not file_path.is_file() or not is_supported(str(file_path)):
            continue

        existing = db.query(PhotoDB).filter(PhotoDB.file_path == str(file_path)).first()
        if existing:
            skipped += 1
            continue

        exif = extract_exif(str(file_path))
        stat = file_path.stat()

        thumb_name = f"{file_path.stem}_{hash(str(file_path))}_thumb.jpg"
        thumb_path = str(thumb_dir / thumb_name)
        generate_thumbnail(str(file_path), thumb_path, thumb_size)

        photo = PhotoDB(
            file_path=str(file_path),
            file_name=file_path.name,
            file_size=stat.st_size,
            width=exif.width,
            height=exif.height,
            shot_at=exif.shot_at,
            camera_make=exif.camera_make,
            camera_model=exif.camera_model,
            lens_model=exif.lens_model,
            focal_length=exif.focal_length,
            aperture=exif.aperture,
            shutter_speed=exif.shutter_speed,
            iso=exif.iso,
            gps_lat=exif.gps_lat,
            gps_lon=exif.gps_lon,
            gps_altitude=exif.gps_altitude,
            thumbnail_path=thumb_path if Path(thumb_path).exists() else None,
        )
        db.add(photo)
        added += 1

    db.commit()
    return {"added": added, "skipped": skipped}


# ── AI Analysis ──────────────────────────────────────────────────────────────

@app.post("/api/analyze")
def analyze_photos(req: AnalyzeRequest, db: Session = Depends(get_db)):
    cfg = config.load()
    api_key = cfg.get("anthropic_api_key", "")
    if not api_key:
        raise HTTPException(400, "Anthropic API key not configured")

    results = []
    for photo_id in req.photo_ids:
        photo = db.get(PhotoDB, photo_id)
        if not photo:
            results.append({"id": photo_id, "status": "not_found"})
            continue

        try:
            analysis = analyze_photo(photo.file_path, api_key)
            photo.ai_theme = analysis.theme
            photo.ai_subjects = json.dumps(analysis.subjects, ensure_ascii=False)
            photo.ai_description = analysis.description
            photo.ai_tags = json.dumps(analysis.tags, ensure_ascii=False)
            photo.ai_analyzed_at = datetime.utcnow()
            db.add(photo)
            results.append({"id": photo_id, "status": "ok", "theme": analysis.theme})
        except Exception as e:
            results.append({"id": photo_id, "status": "error", "error": str(e)})

    db.commit()
    return {"results": results}


# ── Cloud Sync ───────────────────────────────────────────────────────────────

@app.post("/api/sync")
def sync_photos(req: SyncRequest, db: Session = Depends(get_db)):
    cfg = config.load()
    for key in ("aws_access_key", "aws_secret_key", "aws_bucket"):
        if not cfg.get(key):
            raise HTTPException(400, f"Cloud not configured: missing {key}")

    syncer = S3Syncer(
        access_key=cfg["aws_access_key"],
        secret_key=cfg["aws_secret_key"],
        bucket=cfg["aws_bucket"],
        region=cfg.get("aws_region", "us-east-1"),
    )

    results = []
    for photo_id in req.photo_ids:
        photo = db.get(PhotoDB, photo_id)
        if not photo:
            results.append({"id": photo_id, "status": "not_found"})
            continue
        try:
            s3_key = f"photos/{photo.shot_at.strftime('%Y/%m/%d') if photo.shot_at else 'unknown'}/{photo.file_name}"
            url = syncer.upload(photo.file_path, s3_key)
            photo.cloud_synced = True
            photo.cloud_url = url
            photo.cloud_synced_at = datetime.utcnow()
            db.add(photo)
            results.append({"id": photo_id, "status": "ok", "url": url})
        except Exception as e:
            results.append({"id": photo_id, "status": "error", "error": str(e)})

    db.commit()
    return {"results": results}


# ── Settings ─────────────────────────────────────────────────────────────────

@app.get("/api/settings")
def get_settings():
    cfg = config.load()
    # Mask secrets
    masked = dict(cfg)
    for k in ("anthropic_api_key", "aws_secret_key"):
        if masked.get(k):
            masked[k] = "••••••••" + masked[k][-4:]
    return masked


@app.put("/api/settings")
def update_settings(body: SettingsUpdate):
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    cfg = config.save(updates)
    return {"ok": True}


# ── Stats ─────────────────────────────────────────────────────────────────────

@app.get("/api/stats")
def get_stats(db: Session = Depends(get_db)):
    total = db.query(PhotoDB).count()
    analyzed = db.query(PhotoDB).filter(PhotoDB.ai_analyzed_at.isnot(None)).count()
    synced = db.query(PhotoDB).filter(PhotoDB.cloud_synced.is_(True)).count()

    themes_raw = (
        db.query(PhotoDB.ai_theme)
        .filter(PhotoDB.ai_theme.isnot(None))
        .all()
    )
    from collections import Counter
    theme_counts = Counter(row[0] for row in themes_raw)

    cameras_raw = (
        db.query(PhotoDB.camera_model)
        .filter(PhotoDB.camera_model.isnot(None))
        .all()
    )
    camera_counts = Counter(row[0] for row in cameras_raw)

    return {
        "total": total,
        "analyzed": analyzed,
        "synced": synced,
        "themes": dict(theme_counts.most_common(10)),
        "cameras": dict(camera_counts.most_common(5)),
    }
