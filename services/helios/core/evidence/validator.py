import os
from typing import Dict
from helios.infrastructure.encryption import EncryptionManager
import hashlib

def verify_evidence(file_path: str, expected_hash: str) -> Dict[str, any]:
    """
    Verifies that the file on disk matches the expected hash.
    Used for Chain of Custody integrity checks.
    """
    if not os.path.exists(file_path):
        return {
            "valid": False,
            "error": "File not found on disk."
        }
        
    try:
        with open(file_path, "rb") as f:
            encrypted_data = f.read()
            
        enc_manager = EncryptionManager()
        plaintext = enc_manager.decrypt_data(encrypted_data)
        
        sha256 = hashlib.sha256()
        sha256.update(plaintext)
        current_hash = sha256.hexdigest()
    except Exception as e:
        return {
            "valid": False,
            "error": f"Failed to decrypt or verify: {e}"
        }
        
    is_valid = current_hash == expected_hash
    
    return {
        "valid": is_valid,
        "current_hash": current_hash,
        "expected_hash": expected_hash
    }
