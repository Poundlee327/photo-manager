from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class PhotoDB(Base):
    __tablename__ = "photos"

    id = Column(Integer, primary_key=True, index=True)
    file_path = Column(String, unique=True, index=True, nullable=False)
    file_name = Column(String, nullable=False)
    file_size = Column(Integer)
    width = Column(Integer)
    height = Column(Integer)

    # EXIF
    shot_at = Column(DateTime, nullable=True)
    camera_make = Column(String, nullable=True)
    camera_model = Column(String, nullable=True)
    lens_model = Column(String, nullable=True)
    focal_length = Column(String, nullable=True)
    aperture = Column(String, nullable=True)
    shutter_speed = Column(String, nullable=True)
    iso = Column(Integer, nullable=True)
    gps_lat = Column(Float, nullable=True)
    gps_lon = Column(Float, nullable=True)
    gps_altitude = Column(Float, nullable=True)

    # AI analysis
    ai_theme = Column(String, nullable=True)
    ai_subjects = Column(Text, nullable=True)   # JSON list
    ai_description = Column(Text, nullable=True)
    ai_tags = Column(Text, nullable=True)        # JSON list
    ai_analyzed_at = Column(DateTime, nullable=True)

    # Cloud
    cloud_synced = Column(Boolean, default=False)
    cloud_url = Column(String, nullable=True)
    cloud_synced_at = Column(DateTime, nullable=True)

    imported_at = Column(DateTime, default=datetime.utcnow)
    thumbnail_path = Column(String, nullable=True)


# --- Pydantic schemas ---

class ExifInfo(BaseModel):
    shot_at: Optional[datetime] = None
    camera_make: Optional[str] = None
    camera_model: Optional[str] = None
    lens_model: Optional[str] = None
    focal_length: Optional[str] = None
    aperture: Optional[str] = None
    shutter_speed: Optional[str] = None
    iso: Optional[int] = None
    gps_lat: Optional[float] = None
    gps_lon: Optional[float] = None
    gps_altitude: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None


class AIAnalysis(BaseModel):
    theme: str
    subjects: list[str]
    description: str
    tags: list[str]


class PhotoOut(BaseModel):
    id: int
    file_path: str
    file_name: str
    file_size: Optional[int]
    width: Optional[int]
    height: Optional[int]
    shot_at: Optional[datetime]
    camera_make: Optional[str]
    camera_model: Optional[str]
    lens_model: Optional[str]
    focal_length: Optional[str]
    aperture: Optional[str]
    shutter_speed: Optional[str]
    iso: Optional[int]
    gps_lat: Optional[float]
    gps_lon: Optional[float]
    ai_theme: Optional[str]
    ai_subjects: Optional[str]
    ai_description: Optional[str]
    ai_tags: Optional[str]
    ai_analyzed_at: Optional[datetime]
    cloud_synced: bool
    cloud_url: Optional[str]
    thumbnail_path: Optional[str]
    imported_at: datetime

    class Config:
        from_attributes = True


class ScanRequest(BaseModel):
    directory: str
    recursive: bool = True


class AnalyzeRequest(BaseModel):
    photo_ids: list[int]


class SyncRequest(BaseModel):
    photo_ids: list[int]


class SettingsUpdate(BaseModel):
    anthropic_api_key: Optional[str] = None
    aws_access_key: Optional[str] = None
    aws_secret_key: Optional[str] = None
    aws_bucket: Optional[str] = None
    aws_region: Optional[str] = None
    thumbnail_size: Optional[int] = None
