import os, uuid
import boto3

S3_ENDPOINT = os.getenv("S3_ENDPOINT")
S3_REGION = os.getenv("S3_REGION", "auto")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")
S3_BUCKET = os.getenv("S3_BUCKET")
S3_PRESIGN_EXPIRE = int(os.getenv("S3_PRESIGN_EXPIRE", "3600"))
S3_PUBLIC_BASE_URL = os.getenv("S3_PUBLIC_BASE_URL", "")

_session = boto3.session.Session()
_s3 = _session.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY,
    region_name=S3_REGION,
)

def make_key(room_id: str, filename: str) -> str:
    safe = filename.replace("\\", "_").replace("/", "_")
    return f"rooms/{room_id}/{uuid.uuid4()}_{safe}"

def presign_put(key: str, content_type: str) -> str:
    return _s3.generate_presigned_url(
        ClientMethod="put_object",
        Params={"Bucket": S3_BUCKET, "Key": key, "ContentType": content_type},
        ExpiresIn=S3_PRESIGN_EXPIRE,
    )

def presign_get(key: str) -> str:
    return _s3.generate_presigned_url(
        ClientMethod="get_object",
        Params={"Bucket": S3_BUCKET, "Key": key},
        ExpiresIn=S3_PRESIGN_EXPIRE,
    )

def public_url(key: str) -> str:
    if S3_PUBLIC_BASE_URL:
        base = S3_PUBLIC_BASE_URL.rstrip("/")
        return f"{base}/{key}"
    return ""
