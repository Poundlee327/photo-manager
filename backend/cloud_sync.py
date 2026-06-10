"""
Multi-provider cloud storage sync.

Supported:
  s3      — AWS S3
  oss     — 阿里云 OSS
  cos     — 腾讯云 COS
  qiniu   — 七牛云 Kodo
  baidu   — 百度网盘 (Open Platform OAuth2)

Not supported:
  quark   — 夸克云盘（无公开第三方开发者 API，无法实现程序化上传）
"""

import hashlib
import json
import math
import time
from pathlib import Path
from typing import Optional

import requests


def _content_type(path: str) -> str:
    return {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".png": "image/png", ".gif": "image/gif",
        ".webp": "image/webp", ".tiff": "image/tiff", ".tif": "image/tiff",
    }.get(Path(path).suffix.lower(), "application/octet-stream")


def _s3_key(file_path: str, shot_at) -> str:
    date_part = shot_at.strftime("%Y/%m/%d") if shot_at else "unknown"
    return f"photos/{date_part}/{Path(file_path).name}"


# ── AWS S3 ────────────────────────────────────────────────────────────────────

class S3Syncer:
    name = "AWS S3"

    def __init__(self, cfg: dict):
        import boto3
        self.bucket = cfg["s3_bucket"]
        self.client = boto3.client(
            "s3",
            aws_access_key_id=cfg["s3_access_key"],
            aws_secret_access_key=cfg["s3_secret_key"],
            region_name=cfg.get("s3_region", "us-east-1"),
        )

    def upload(self, local_path: str, shot_at=None) -> str:
        key = _s3_key(local_path, shot_at)
        self.client.upload_file(local_path, self.bucket, key,
                                ExtraArgs={"ContentType": _content_type(local_path)})
        return f"https://{self.bucket}.s3.amazonaws.com/{key}"


# ── 阿里云 OSS ─────────────────────────────────────────────────────────────────

class AliyunOSSSyncer:
    name = "阿里云 OSS"

    def __init__(self, cfg: dict):
        import oss2
        auth = oss2.Auth(cfg["oss_access_key_id"], cfg["oss_access_key_secret"])
        self.bucket = oss2.Bucket(auth, cfg["oss_endpoint"], cfg["oss_bucket"])
        self.bucket_name = cfg["oss_bucket"]
        self.endpoint = cfg["oss_endpoint"].rstrip("/")

    def upload(self, local_path: str, shot_at=None) -> str:
        key = _s3_key(local_path, shot_at)
        self.bucket.put_object_from_file(key, local_path)
        return f"https://{self.bucket_name}.{self.endpoint.split('://')[-1]}/{key}"


# ── 腾讯云 COS ─────────────────────────────────────────────────────────────────

class TencentCOSSyncer:
    name = "腾讯云 COS"

    def __init__(self, cfg: dict):
        from qcloud_cos import CosConfig, CosS3Client
        config = CosConfig(
            Region=cfg["cos_region"],
            SecretId=cfg["cos_secret_id"],
            SecretKey=cfg["cos_secret_key"],
        )
        self.client = CosS3Client(config)
        self.bucket = cfg["cos_bucket"]
        self.region = cfg["cos_region"]

    def upload(self, local_path: str, shot_at=None) -> str:
        key = _s3_key(local_path, shot_at)
        self.client.upload_file(Bucket=self.bucket, Key=key, LocalFilePath=local_path)
        return f"https://{self.bucket}.cos.{self.region}.myqcloud.com/{key}"


# ── 七牛云 Kodo ────────────────────────────────────────────────────────────────

class QiniuSyncer:
    name = "七牛云 Kodo"

    def __init__(self, cfg: dict):
        import qiniu
        self.q = qiniu.Auth(cfg["qiniu_access_key"], cfg["qiniu_secret_key"])
        self.bucket = cfg["qiniu_bucket"]
        self.domain = cfg["qiniu_domain"].rstrip("/")

    def upload(self, local_path: str, shot_at=None) -> str:
        import qiniu
        key = _s3_key(local_path, shot_at)
        token = self.q.upload_token(self.bucket, key)
        ret, info = qiniu.put_file(token, key, local_path)
        if info.status_code != 200:
            raise RuntimeError(f"七牛上传失败: {info}")
        return f"{self.domain}/{key}"


# ── 百度网盘 ──────────────────────────────────────────────────────────────────

BAIDU_API = "https://pan.baidu.com/rest/2.0/xpan/file"
BAIDU_PCS = "https://d.pcs.baidu.com/rest/2.0/pcs/superfile2"
BLOCK_SIZE = 4 * 1024 * 1024  # 4 MB per block


def _md5(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


class BaiduNetdiskSyncer:
    name = "百度网盘"

    def __init__(self, cfg: dict):
        self.access_token = cfg["baidu_access_token"]
        self.save_dir = cfg.get("baidu_save_dir", "/PhotoLib").rstrip("/")

    def upload(self, local_path: str, shot_at=None) -> str:
        fname = Path(local_path).name
        date_part = shot_at.strftime("%Y/%m/%d") if shot_at else "unknown"
        remote_path = f"{self.save_dir}/{date_part}/{fname}"

        with open(local_path, "rb") as f:
            data = f.read()

        file_size = len(data)
        blocks = [data[i:i + BLOCK_SIZE] for i in range(0, file_size, BLOCK_SIZE)]
        block_md5s = [_md5(b) for b in blocks]
        file_md5 = _md5(data)

        # Step 1: precreate
        pre_resp = requests.post(
            BAIDU_API,
            params={"method": "precreate", "access_token": self.access_token},
            data={
                "path": remote_path,
                "size": file_size,
                "isdir": 0,
                "autoinit": 1,
                "rtype": 1,
                "block_list": json.dumps(block_md5s),
                "content-md5": file_md5,
            },
        )
        pre_resp.raise_for_status()
        pre = pre_resp.json()
        if pre.get("errno", 0) != 0:
            raise RuntimeError(f"百度网盘预创建失败: {pre}")
        upload_id = pre["uploadid"]

        # Step 2: upload each block
        for i, block in enumerate(blocks):
            up_resp = requests.post(
                BAIDU_PCS,
                params={
                    "method": "upload",
                    "access_token": self.access_token,
                    "type": "tmpfile",
                    "path": remote_path,
                    "uploadid": upload_id,
                    "partseq": i,
                },
                files={"file": (fname, block, "application/octet-stream")},
            )
            up_resp.raise_for_status()

        # Step 3: create (finalize)
        create_resp = requests.post(
            BAIDU_API,
            params={"method": "create", "access_token": self.access_token},
            data={
                "path": remote_path,
                "size": file_size,
                "isdir": 0,
                "rtype": 1,
                "uploadid": upload_id,
                "block_list": json.dumps(block_md5s),
            },
        )
        create_resp.raise_for_status()
        result = create_resp.json()
        if result.get("errno", 0) != 0:
            raise RuntimeError(f"百度网盘创建失败: {result}")

        return f"https://pan.baidu.com/s/ (已上传至 {remote_path})"


# ── OAuth helpers for Baidu ───────────────────────────────────────────────────

def baidu_get_auth_url(app_key: str) -> str:
    return (
        f"https://openapi.baidu.com/oauth/2.0/authorize"
        f"?response_type=code&client_id={app_key}"
        f"&redirect_uri=oob&scope=basic,netdisk&display=popup"
    )


def baidu_exchange_code(app_key: str, secret_key: str, code: str) -> dict:
    resp = requests.get(
        "https://openapi.baidu.com/oauth/2.0/token",
        params={
            "grant_type": "authorization_code",
            "code": code,
            "client_id": app_key,
            "client_secret": secret_key,
            "redirect_uri": "oob",
        },
    )
    resp.raise_for_status()
    data = resp.json()
    if "access_token" not in data:
        raise RuntimeError(f"百度授权失败: {data}")
    return data  # contains access_token, refresh_token, expires_in


def baidu_refresh_token(app_key: str, secret_key: str, refresh_token: str) -> dict:
    resp = requests.get(
        "https://openapi.baidu.com/oauth/2.0/token",
        params={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": app_key,
            "client_secret": secret_key,
        },
    )
    resp.raise_for_status()
    return resp.json()


# ── Factory ───────────────────────────────────────────────────────────────────

PROVIDER_MAP = {
    "s3": S3Syncer,
    "oss": AliyunOSSSyncer,
    "cos": TencentCOSSyncer,
    "qiniu": QiniuSyncer,
    "baidu": BaiduNetdiskSyncer,
}

REQUIRED_KEYS = {
    "s3":    ["s3_access_key", "s3_secret_key", "s3_bucket"],
    "oss":   ["oss_access_key_id", "oss_access_key_secret", "oss_bucket", "oss_endpoint"],
    "cos":   ["cos_secret_id", "cos_secret_key", "cos_bucket", "cos_region"],
    "qiniu": ["qiniu_access_key", "qiniu_secret_key", "qiniu_bucket", "qiniu_domain"],
    "baidu": ["baidu_access_token"],
}


def get_syncer(cfg: dict):
    provider = cfg.get("cloud_provider", "s3")
    if provider not in PROVIDER_MAP:
        raise ValueError(f"未知云存储提供商: {provider}。可选: {', '.join(PROVIDER_MAP)}")
    missing = [k for k in REQUIRED_KEYS.get(provider, []) if not cfg.get(k)]
    if missing:
        raise ValueError(f"{provider} 缺少配置项: {', '.join(missing)}")
    return PROVIDER_MAP[provider](cfg)
