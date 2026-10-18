import hashlib
import secrets
import string

_ALPHABET = string.ascii_letters + string.digits


def generate(prefix="sk_live_"):
    return prefix + "".join(secrets.choice(_ALPHABET) for _ in range(24))


def hash_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


def verify_key(key: str, h: str) -> bool:
    return hash_key(key) == h
