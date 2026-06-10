"""
Multi-provider AI image analyzer.

Vision providers (can analyze image pixels):
  claude   — Anthropic Claude claude-sonnet-4-6
  openai   — OpenAI GPT-4o

Metadata providers (no vision API; infer from EXIF + filename):
  deepseek — DeepSeek-Chat (OpenAI-compatible endpoint)
"""

import base64
import json
from pathlib import Path
from typing import Optional

from models import AIAnalysis


# ── Shared ────────────────────────────────────────────────────────────────────

VISION_PROMPT = """请分析这张照片，以 JSON 格式返回以下字段（不要加 markdown 代码块）：
{
  "theme": "主题分类（如：风光、人像、街头、建筑、生态、美食、运动、天文等）",
  "subjects": ["主体元素列表，最多5个"],
  "description": "一句话简洁描述这张照片的内容和氛围（中文，30字以内）",
  "tags": ["关键词标签列表，最多10个，包含场景、颜色、情绪、技法等维度"]
}
请只返回 JSON，不要其他文字。"""


def _encode_image(file_path: str) -> tuple[str, str]:
    ext = Path(file_path).suffix.lower()
    media_map = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".png": "image/png", ".gif": "image/gif", ".webp": "image/webp",
    }
    media_type = media_map.get(ext, "image/jpeg")
    with open(file_path, "rb") as f:
        data = base64.standard_b64encode(f.read()).decode("utf-8")
    return data, media_type


def _source_path(file_path: str) -> str:
    """Prefer thumbnail to save tokens/cost."""
    stem = Path(file_path).stem
    thumb = Path(file_path).parent / f"{stem}_thumb.jpg"
    return str(thumb) if thumb.exists() else file_path


def _parse_json(raw: str) -> dict:
    raw = raw.strip()
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1].lstrip("json").strip() if len(parts) > 1 else raw
    return json.loads(raw)


def _to_analysis(parsed: dict) -> AIAnalysis:
    return AIAnalysis(
        theme=parsed.get("theme", "未知"),
        subjects=parsed.get("subjects", []),
        description=parsed.get("description", ""),
        tags=parsed.get("tags", []),
    )


# ── Claude ────────────────────────────────────────────────────────────────────

def _analyze_claude(file_path: str, api_key: str, model: str) -> AIAnalysis:
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    src = _source_path(file_path)
    image_data, media_type = _encode_image(src)

    response = client.messages.create(
        model=model,
        max_tokens=512,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": image_data}},
                {"type": "text", "text": VISION_PROMPT},
            ],
        }],
    )
    return _to_analysis(_parse_json(response.content[0].text))


# ── OpenAI GPT-4o ─────────────────────────────────────────────────────────────

def _analyze_openai(file_path: str, api_key: str, model: str) -> AIAnalysis:
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    src = _source_path(file_path)
    image_data, media_type = _encode_image(src)
    data_url = f"data:{media_type};base64,{image_data}"

    response = client.chat.completions.create(
        model=model,
        max_tokens=512,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": data_url, "detail": "low"}},
                {"type": "text", "text": VISION_PROMPT},
            ],
        }],
    )
    return _to_analysis(_parse_json(response.choices[0].message.content))


# ── DeepSeek (text-only, metadata inference) ──────────────────────────────────

def _analyze_deepseek(file_path: str, api_key: str, model: str, exif_meta: Optional[dict] = None) -> AIAnalysis:
    """
    DeepSeek has no public vision API; we infer theme from EXIF + filename.
    Pass exif_meta dict with keys: shot_at, camera_model, lens_model,
    focal_length, aperture, shutter_speed, iso, gps_lat, gps_lon.
    """
    from openai import OpenAI
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    meta = exif_meta or {}

    text_prompt = f"""你是专业摄影分析师。根据以下照片元数据推断照片主题和内容：

文件名：{Path(file_path).name}
拍摄时间：{meta.get('shot_at', '未知')}
相机：{meta.get('camera_model', '未知')}
镜头：{meta.get('lens_model', '未知')}
焦距：{meta.get('focal_length', '未知')}
光圈：{meta.get('aperture', '未知')}
快门：{meta.get('shutter_speed', '未知')}
ISO：{meta.get('iso', '未知')}
GPS：{f"{meta.get('gps_lat'):.4f}, {meta.get('gps_lon'):.4f}" if meta.get('gps_lat') else '无'}

请以 JSON 格式返回（不要加代码块）：
{{"theme":"主题","subjects":["主体1","主体2"],"description":"描述","tags":["标签1","标签2"]}}"""

    response = client.chat.completions.create(
        model=model,
        max_tokens=256,
        messages=[{"role": "user", "content": text_prompt}],
    )
    return _to_analysis(_parse_json(response.choices[0].message.content))


# ── Public API ────────────────────────────────────────────────────────────────

PROVIDER_DEFAULTS = {
    "claude":   "claude-sonnet-4-6",
    "openai":   "gpt-4o",
    "deepseek": "deepseek-chat",
}


def analyze_photo(
    file_path: str,
    provider: str,
    api_key: str,
    model: Optional[str] = None,
    exif_meta: Optional[dict] = None,
) -> AIAnalysis:
    model = model or PROVIDER_DEFAULTS.get(provider, "")

    if provider == "claude":
        return _analyze_claude(file_path, api_key, model)
    elif provider == "openai":
        return _analyze_openai(file_path, api_key, model)
    elif provider == "deepseek":
        return _analyze_deepseek(file_path, api_key, model, exif_meta)
    else:
        raise ValueError(f"未知 AI 提供商: {provider}。可选: claude / openai / deepseek")
