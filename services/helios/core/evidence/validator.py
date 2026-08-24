import os
from typing import Dict
from helios.core.evidence.manager import calculate_hash

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
        
    current_hash = calculate_hash(file_path)
    is_valid = current_hash == expected_hash
    
    return {
        "valid": is_valid,
        "current_hash": current_hash,
        "expected_hash": expected_hash
    }
