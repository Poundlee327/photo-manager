import json
from pathlib import Path

CONFIG_PATH = Path.home() / ".photo-manager" / "config.json"
CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)

DEFAULTS = {
    # AI
    "ai_provider": "claude",           # claude | openai | deepseek
    "anthropic_api_key": "",
    "anthropic_model": "claude-sonnet-4-6",
    "openai_api_key": "",
    "openai_model": "gpt-4o",
    "deepseek_api_key": "",
    "deepseek_model": "deepseek-chat",

    # Cloud storage
    "cloud_provider": "s3",            # s3 | oss | cos | qiniu | baidu

    # AWS S3
    "s3_access_key": "",
    "s3_secret_key": "",
    "s3_bucket": "",
    "s3_region": "us-east-1",

    # 阿里云 OSS
    "oss_access_key_id": "",
    "oss_access_key_secret": "",
    "oss_bucket": "",
    "oss_endpoint": "oss-cn-hangzhou.aliyuncs.com",

    # 腾讯云 COS
    "cos_secret_id": "",
    "cos_secret_key": "",
    "cos_bucket": "",
    "cos_region": "ap-beijing",

    # 七牛云 Kodo
    "qiniu_access_key": "",
    "qiniu_secret_key": "",
    "qiniu_bucket": "",
    "qiniu_domain": "",

    # 百度网盘
    "baidu_app_key": "",
    "baidu_secret_key": "",
    "baidu_access_token": "",
    "baidu_refresh_token": "",
    "baidu_save_dir": "/PhotoLib",

    # App
    "thumbnail_size": 400,
    "thumbnail_dir": str(Path.home() / ".photo-manager" / "thumbnails"),
}

SECRET_KEYS = {
    "anthropic_api_key", "openai_api_key", "deepseek_api_key",
    "s3_secret_key", "oss_access_key_secret", "cos_secret_key",
    "qiniu_secret_key", "baidu_secret_key", "baidu_access_token", "baidu_refresh_token",
}


def load() -> dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, encoding="utf-8") as f:
            stored = json.load(f)
        return {**DEFAULTS, **stored}
    return dict(DEFAULTS)


def save(updates: dict) -> dict:
    current = load()
    current.update(updates)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(current, f, indent=2, ensure_ascii=False)
    return current


def masked() -> dict:
    cfg = load()
    result = dict(cfg)
    for k in SECRET_KEYS:
        v = result.get(k, "")
        if v:
            result[k] = "••••••••" + v[-4:]
    return result
