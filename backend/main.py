import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

import config
from ai_analyzer import analyze_photo
from cloud_sync import baidu_exchange_code, baidu_get_auth_url, baidu_refresh_token, get_syncer
from database import get_db, init_db
from exif_parser import extract_exif, generate_thumbnail, is_supported
from models import (
    AnalyzeRequest,
    BaiduCodeRequest,
    PhotoDB,
    PhotoOut,
    ScanRequest,
    SettingsUpdate,
    SyncRequest,
)

app = FastAPI(title="Photo Manager API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()
Path(config.load()["thumbnail_dir"]).mkdir(parents=True, exist_ok=True)


# ── Photos ────────────────────────────────────────────────────────────────────

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


# ── Scan ──────────────────────────────────────────────────────────────────────

@app.post("/api/scan")
def scan_directory(req: ScanRequest, db: Session = Depends(get_db)):
    base = Path(req.directory)
    if not base.exists():
        raise HTTPException(400, f"目录不存在: {req.directory}")

    cfg = config.load()
    thumb_dir = Path(cfg["thumbnail_dir"])
    thumb_size = cfg["thumbnail_size"]
    pattern = "**/*" if req.recursive else "*"
    added, skipped = 0, 0

    for file_path in base.glob(pattern):
        if not file_path.is_file() or not is_supported(str(file_path)):
            continue
        if db.query(PhotoDB).filter(PhotoDB.file_path == str(file_path)).first():
            skipped += 1
            continue

        exif = extract_exif(str(file_path))
        stat = file_path.stat()
        thumb_name = f"{file_path.stem}_{abs(hash(str(file_path)))}_thumb.jpg"
        thumb_path = str(thumb_dir / thumb_name)
        generate_thumbnail(str(file_path), thumb_path, thumb_size)

        db.add(PhotoDB(
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
        ))
        added += 1

    db.commit()
    return {"added": added, "skipped": skipped}


# ── AI Analysis ───────────────────────────────────────────────────────────────

@app.post("/api/analyze")
def analyze_photos(req: AnalyzeRequest, db: Session = Depends(get_db)):
    cfg = config.load()
    provider = cfg.get("ai_provider", "claude")

    key_map = {
        "claude":   "anthropic_api_key",
        "openai":   "openai_api_key",
        "deepseek": "deepseek_api_key",
    }
    model_map = {
        "claude":   "anthropic_model",
        "openai":   "openai_model",
        "deepseek": "deepseek_model",
    }

    api_key = cfg.get(key_map.get(provider, ""), "")
    if not api_key:
        raise HTTPException(400, f"{provider} API Key 未配置，请先在设置页填写")
    model = cfg.get(model_map.get(provider, ""), "")

    results = []
    for photo_id in req.photo_ids:
        photo = db.get(PhotoDB, photo_id)
        if not photo:
            results.append({"id": photo_id, "status": "not_found"})
            continue
        try:
            exif_meta = {
                "shot_at": str(photo.shot_at) if photo.shot_at else None,
                "camera_model": photo.camera_model,
                "lens_model": photo.lens_model,
                "focal_length": photo.focal_length,
                "aperture": photo.aperture,
                "shutter_speed": photo.shutter_speed,
                "iso": photo.iso,
                "gps_lat": photo.gps_lat,
                "gps_lon": photo.gps_lon,
            }
            analysis = analyze_photo(photo.file_path, provider, api_key, model, exif_meta)
            photo.ai_theme = analysis.theme
            photo.ai_subjects = json.dumps(analysis.subjects, ensure_ascii=False)
            photo.ai_description = analysis.description
            photo.ai_tags = json.dumps(analysis.tags, ensure_ascii=False)
            photo.ai_analyzed_at = datetime.utcnow()
            photo.ai_provider = f"{provider}/{model}"
            db.add(photo)
            results.append({"id": photo_id, "status": "ok", "theme": analysis.theme})
        except Exception as e:
            results.append({"id": photo_id, "status": "error", "error": str(e)})

    db.commit()
    return {"results": results}


# ── Cloud Sync ────────────────────────────────────────────────────────────────

@app.post("/api/sync")
def sync_photos(req: SyncRequest, db: Session = Depends(get_db)):
    cfg = config.load()
    try:
        syncer = get_syncer(cfg)
    except ValueError as e:
        raise HTTPException(400, str(e))

    results = []
    for photo_id in req.photo_ids:
        photo = db.get(PhotoDB, photo_id)
        if not photo:
            results.append({"id": photo_id, "status": "not_found"})
            continue
        try:
            url = syncer.upload(photo.file_path, photo.shot_at)
            photo.cloud_synced = True
            photo.cloud_url = url
            photo.cloud_provider = cfg.get("cloud_provider")
            photo.cloud_synced_at = datetime.utcnow()
            db.add(photo)
            results.append({"id": photo_id, "status": "ok", "url": url})
        except Exception as e:
            results.append({"id": photo_id, "status": "error", "error": str(e)})

    db.commit()
    return {"results": results}


# ── Baidu OAuth ───────────────────────────────────────────────────────────────

@app.get("/api/auth/baidu/url")
def baidu_auth_url():
    cfg = config.load()
    app_key = cfg.get("baidu_app_key", "")
    if not app_key:
        raise HTTPException(400, "请先在设置中填写百度网盘 App Key")
    return {"url": baidu_get_auth_url(app_key)}


@app.post("/api/auth/baidu/exchange")
def baidu_auth_exchange(body: BaiduCodeRequest):
    cfg = config.load()
    app_key = cfg.get("baidu_app_key", "")
    secret_key = cfg.get("baidu_secret_key", "")
    if not app_key or not secret_key:
        raise HTTPException(400, "请先填写百度网盘 App Key 和 Secret Key")
    try:
        tokens = baidu_exchange_code(app_key, secret_key, body.code)
        config.save({
            "baidu_access_token": tokens["access_token"],
            "baidu_refresh_token": tokens.get("refresh_token", ""),
        })
        return {"ok": True, "expires_in": tokens.get("expires_in")}
    except Exception as e:
        raise HTTPException(400, f"授权失败: {e}")


@app.post("/api/auth/baidu/refresh")
def baidu_auth_refresh():
    cfg = config.load()
    try:
        tokens = baidu_refresh_token(cfg["baidu_app_key"], cfg["baidu_secret_key"], cfg["baidu_refresh_token"])
        config.save({
            "baidu_access_token": tokens["access_token"],
            "baidu_refresh_token": tokens.get("refresh_token", cfg["baidu_refresh_token"]),
        })
        return {"ok": True}
    except Exception as e:
        raise HTTPException(400, f"刷新失败: {e}")


# ── Settings ──────────────────────────────────────────────────────────────────

@app.get("/api/settings")
def get_settings():
    return config.masked()


@app.put("/api/settings")
def update_settings(body: SettingsUpdate):
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    config.save(updates)
    return {"ok": True}


@app.get("/api/settings/providers")
def get_providers():
    """Return which AI and cloud providers are configured."""
    cfg = config.load()
    return {
        "ai": {
            "current": cfg.get("ai_provider", "claude"),
            "configured": {
                "claude":   bool(cfg.get("anthropic_api_key")),
                "openai":   bool(cfg.get("openai_api_key")),
                "deepseek": bool(cfg.get("deepseek_api_key")),
            },
        },
        "cloud": {
            "current": cfg.get("cloud_provider", "s3"),
            "configured": {
                "s3":    bool(cfg.get("s3_access_key") and cfg.get("s3_bucket")),
                "oss":   bool(cfg.get("oss_access_key_id") and cfg.get("oss_bucket")),
                "cos":   bool(cfg.get("cos_secret_id") and cfg.get("cos_bucket")),
                "qiniu": bool(cfg.get("qiniu_access_key") and cfg.get("qiniu_bucket")),
                "baidu": bool(cfg.get("baidu_access_token")),
            },
        },
    }


# ── Stats ─────────────────────────────────────────────────────────────────────

@app.get("/api/stats")
def get_stats(db: Session = Depends(get_db)):
    total    = db.query(PhotoDB).count()
    analyzed = db.query(PhotoDB).filter(PhotoDB.ai_analyzed_at.isnot(None)).count()
    synced   = db.query(PhotoDB).filter(PhotoDB.cloud_synced.is_(True)).count()

    theme_counts = Counter(
        r[0] for r in db.query(PhotoDB.ai_theme).filter(PhotoDB.ai_theme.isnot(None)).all()
    )
    camera_counts = Counter(
        r[0] for r in db.query(PhotoDB.camera_model).filter(PhotoDB.camera_model.isnot(None)).all()
    )
    return {
        "total": total,
        "analyzed": analyzed,
        "synced": synced,
        "themes": dict(theme_counts.most_common(10)),
        "cameras": dict(camera_counts.most_common(5)),
    }
