import os
import hashlib
import uuid
import shutil
from pathlib import Path
from fastapi import UploadFile

EVIDENCE_DIR = Path(".helios_storage/evidence")

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

def save_evidence_file(upload_file: UploadFile) -> dict:
    """
    Saves an uploaded file to disk and calculates its hash.
    Returns the file path and hash.
    """
    init_storage()
    
    # Generate a unique filename to prevent collisions, but keep original extension
    ext = os.path.splitext(upload_file.filename)[1] if upload_file.filename else ""
    unique_filename = f"{uuid.uuid4()}{ext}"
    file_path = EVIDENCE_DIR / unique_filename
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
        
    file_hash = calculate_hash(str(file_path))
    
    return {
        "file_path": str(file_path),
        "file_hash": file_hash,
        "original_filename": upload_file.filename
    }
