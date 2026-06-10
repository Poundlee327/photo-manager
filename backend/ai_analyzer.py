import base64
import json
import os
from pathlib import Path

import anthropic

from models import AIAnalysis


def _encode_image(file_path: str) -> tuple[str, str]:
    """Return (base64_data, media_type)."""
    ext = Path(file_path).suffix.lower()
    media_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    media_type = media_map.get(ext, "image/jpeg")
    with open(file_path, "rb") as f:
        data = base64.standard_b64encode(f.read()).decode("utf-8")
    return data, media_type


ANALYSIS_PROMPT = """请分析这张照片，以 JSON 格式返回以下字段（不要加 markdown 代码块）：
{
  "theme": "主题分类（如：风光、人像、街头、建筑、生态、美食、运动、天文等）",
  "subjects": ["主体元素列表，最多5个"],
  "description": "一句话简洁描述这张照片的内容和氛围（中文，30字以内）",
  "tags": ["关键词标签列表，最多10个，包含场景、颜色、情绪、技法等维度"]
}

请只返回 JSON，不要其他文字。"""


def analyze_photo(file_path: str, api_key: str) -> AIAnalysis:
    """Send photo to Claude and return structured analysis."""
    client = anthropic.Anthropic(api_key=api_key)

    # Use thumbnail if available to save tokens
    thumb_path = file_path.replace(Path(file_path).suffix, "_thumb.jpg")
    source_path = thumb_path if Path(thumb_path).exists() else file_path

    image_data, media_type = _encode_image(source_path)

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data,
                        },
                    },
                    {"type": "text", "text": ANALYSIS_PROMPT},
                ],
            }
        ],
    )

    raw = response.content[0].text.strip()

    # Strip markdown fences if model adds them
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    parsed = json.loads(raw)
    return AIAnalysis(
        theme=parsed.get("theme", "未知"),
        subjects=parsed.get("subjects", []),
        description=parsed.get("description", ""),
        tags=parsed.get("tags", []),
    )
