import json
from pathlib import Path

CONFIG_PATH = Path.home() / ".photo-manager" / "config.json"
CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)

DEFAULTS = {
    "anthropic_api_key": "",
    "aws_access_key": "",
    "aws_secret_key": "",
    "aws_bucket": "",
    "aws_region": "us-east-1",
    "thumbnail_size": 400,
    "thumbnail_dir": str(Path.home() / ".photo-manager" / "thumbnails"),
}


def load() -> dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            stored = json.load(f)
        return {**DEFAULTS, **stored}
    return dict(DEFAULTS)


def save(updates: dict):
    current = load()
    current.update(updates)
    with open(CONFIG_PATH, "w") as f:
        json.dump(current, f, indent=2)
    return current
