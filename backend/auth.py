from __future__ import annotations

from base64 import urlsafe_b64decode, urlsafe_b64encode
from datetime import UTC, datetime, timedelta
import hashlib
import hmac
import json


def issue_token(subject: str, secret: str, ttl_minutes: int) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": subject,
        "exp": int((datetime.now(UTC) + timedelta(minutes=ttl_minutes)).timestamp()),
    }
    return _encode_token(header, payload, secret)


def decode_token(token: str, secret: str) -> dict:
    try:
        header_b64, payload_b64, signature_b64 = token.split(".")
    except ValueError as exc:
        raise ValueError("Malformed token.") from exc
    expected = _sign(f"{header_b64}.{payload_b64}".encode("utf-8"), secret)
    provided = _b64decode(signature_b64)
    if not hmac.compare_digest(expected, provided):
        raise ValueError("Invalid token signature.")

    payload = json.loads(_b64decode(payload_b64))
    if int(payload.get("exp", 0)) < int(datetime.now(UTC).timestamp()):
        raise ValueError("Token expired.")
    return payload


def secure_compare(left: str, right: str) -> bool:
    return hmac.compare_digest(left.encode("utf-8"), right.encode("utf-8"))


def _encode_token(header: dict, payload: dict, secret: str) -> str:
    header_b64 = _b64encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signature = _sign(f"{header_b64}.{payload_b64}".encode("utf-8"), secret)
    return f"{header_b64}.{payload_b64}.{_b64encode(signature)}"


def _sign(value: bytes, secret: str) -> bytes:
    return hmac.new(secret.encode("utf-8"), value, hashlib.sha256).digest()


def _b64encode(value: bytes) -> str:
    return urlsafe_b64encode(value).rstrip(b"=").decode("utf-8")


def _b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return urlsafe_b64decode(value + padding)
