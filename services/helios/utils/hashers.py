import hashlib
import bcrypt


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a bcrypt hashed password."""
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def md5_hash(text: str) -> str:
    """Return MD5 hash of string."""
    return hashlib.md5(text.encode()).hexdigest()


def sha256_hash(text: str) -> str:
    """Return SHA-256 hash of string."""
    return hashlib.sha256(text.encode()).hexdigest()
