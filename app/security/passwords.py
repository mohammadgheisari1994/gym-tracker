"""Password hashing backed by argon2 (via pwdlib)."""

from pwdlib import PasswordHash

_hasher = PasswordHash.recommended()


def hash_password(plain_password: str) -> str:
    return _hasher.hash(plain_password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return _hasher.verify(plain_password, password_hash)
