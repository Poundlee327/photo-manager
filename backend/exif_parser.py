import io
from datetime import datetime
from pathlib import Path
from typing import Optional

import exifread
from PIL import Image

from models import ExifInfo


SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".heic", ".webp", ".raw", ".cr2", ".nef", ".arw"}


def _parse_gps_coord(values) -> Optional[float]:
    """Convert GPS rational values [deg, min, sec] to decimal degrees."""
    try:
        d = float(values[0].num) / float(values[0].den)
        m = float(values[1].num) / float(values[1].den)
        s = float(values[2].num) / float(values[2].den)
        return d + m / 60 + s / 3600
    except Exception:
        return None


def _rational_to_str(value) -> Optional[str]:
    try:
        return str(value)
    except Exception:
        return None


def extract_exif(file_path: str) -> ExifInfo:
    path = Path(file_path)
    info = ExifInfo()

    # Use Pillow for image dimensions
    try:
        with Image.open(file_path) as img:
            info.width, info.height = img.size
    except Exception:
        pass

    # Use exifread for metadata
    try:
        with open(file_path, "rb") as f:
            tags = exifread.process_file(f, stop_tag="GPS GPSLongitude", details=False)

        if not tags:
            return info

        # Shooting date
        for date_tag in ("EXIF DateTimeOriginal", "EXIF DateTimeDigitized", "Image DateTime"):
            if date_tag in tags:
                try:
                    raw = str(tags[date_tag])
                    info.shot_at = datetime.strptime(raw, "%Y:%m:%d %H:%M:%S")
                    break
                except ValueError:
                    continue

        info.camera_make = str(tags["Image Make"]).strip() if "Image Make" in tags else None
        info.camera_model = str(tags["Image Model"]).strip() if "Image Model" in tags else None
        info.lens_model = str(tags.get("EXIF LensModel", tags.get("MakerNote LensType", ""))).strip() or None

        if "EXIF FocalLength" in tags:
            info.focal_length = _rational_to_str(tags["EXIF FocalLength"])

        if "EXIF FNumber" in tags:
            try:
                val = tags["EXIF FNumber"].values[0]
                f_num = float(val.num) / float(val.den)
                info.aperture = f"f/{f_num:.1f}"
            except Exception:
                pass

        if "EXIF ExposureTime" in tags:
            info.shutter_speed = _rational_to_str(tags["EXIF ExposureTime"])

        if "EXIF ISOSpeedRatings" in tags:
            try:
                info.iso = int(str(tags["EXIF ISOSpeedRatings"]))
            except ValueError:
                pass

        # GPS
        if "GPS GPSLatitude" in tags and "GPS GPSLongitude" in tags:
            lat = _parse_gps_coord(tags["GPS GPSLatitude"].values)
            lon = _parse_gps_coord(tags["GPS GPSLongitude"].values)
            if lat is not None and lon is not None:
                lat_ref = str(tags.get("GPS GPSLatitudeRef", "N"))
                lon_ref = str(tags.get("GPS GPSLongitudeRef", "E"))
                info.gps_lat = lat if "N" in lat_ref else -lat
                info.gps_lon = lon if "E" in lon_ref else -lon

        if "GPS GPSAltitude" in tags:
            try:
                val = tags["GPS GPSAltitude"].values[0]
                info.gps_altitude = float(val.num) / float(val.den)
            except Exception:
                pass

    except Exception:
        pass

    # Fallback: use file modification time if no EXIF date
    if info.shot_at is None:
        try:
            mtime = path.stat().st_mtime
            info.shot_at = datetime.fromtimestamp(mtime)
        except Exception:
            pass

    return info


def generate_thumbnail(src_path: str, thumb_path: str, size: int = 400) -> bool:
    try:
        with Image.open(src_path) as img:
            img.thumbnail((size, size), Image.LANCZOS)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.save(thumb_path, "JPEG", quality=80)
        return True
    except Exception:
        return False


def is_supported(file_path: str) -> bool:
    return Path(file_path).suffix.lower() in SUPPORTED_EXTENSIONS
