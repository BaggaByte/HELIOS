import os
import hashlib
import uuid
import shutil
from pathlib import Path
from fastapi import UploadFile, HTTPException, status
from helios.infrastructure.encryption import EncryptionManager
from helios.config import get_settings

settings = get_settings()
EVIDENCE_DIR = Path(settings.UPLOAD_DIR) / "evidence"


def init_storage():
    """Ensure the evidence storage directory exists."""
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)


def calculate_hash(file_path: str) -> str:
    """Calculates SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


async def save_evidence_file(upload_file: UploadFile) -> dict:
    """
    Saves an uploaded file to disk and calculates its original plaintext hash.
    Encrypts the file before saving to prevent plaintext leakage.
    Enforces a strict 50MB file size limit per upload.
    Returns the file path and plaintext hash.
    """
    init_storage()

    # 50MB limit
    MAX_FILE_SIZE = 50 * 1024 * 1024

    # Read file in chunks to enforce memory limit
    file_data = bytearray()
    sha256 = hashlib.sha256()

    while chunk := await upload_file.read(8192):
        file_data.extend(chunk)
        sha256.update(chunk)
        if len(file_data) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File exceeds the maximum limit of 50MB.",
            )

    file_data = bytes(file_data)
    file_hash = sha256.hexdigest()

    # Generate a unique filename to prevent collisions, but keep original extension
    ext = os.path.splitext(upload_file.filename)[1] if upload_file.filename else ""
    unique_filename = f"{uuid.uuid4()}{ext}"
    file_path = EVIDENCE_DIR / unique_filename

    # Encrypt
    enc_manager = EncryptionManager()
    encrypted_data = enc_manager.encrypt_data(file_data)

    # Write encrypted to disk
    with open(file_path, "wb") as buffer:
        buffer.write(encrypted_data)

    return {
        "file_path": str(file_path),
        "file_hash": file_hash,
        "original_filename": upload_file.filename,
    }
