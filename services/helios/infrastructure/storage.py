import os
import aiofiles
from pathlib import Path
from helios.infrastructure.encryption import EncryptionManager

class StorageManager:
    def __init__(self, base_dir: str = "data/uploads"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.encryption = EncryptionManager()
        
    async def save_file(self, filename: str, content: bytes) -> str:
        """Saves a file to disk, encrypting it before writing."""
        file_path = self.base_dir / filename
        
        # Ensure unique filename
        counter = 1
        stem = file_path.stem
        suffix = file_path.suffix
        while file_path.exists():
            file_path = self.base_dir / f"{stem}_{counter}{suffix}"
            counter += 1
            
        encrypted_content = self.encryption.encrypt_data(content)
        
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(encrypted_content)
            
        return str(file_path.absolute())
        
    async def load_file(self, file_path: str) -> bytes:
        """Loads and decrypts a file from disk."""
        async with aiofiles.open(file_path, 'rb') as f:
            encrypted_content = await f.read()
            
        return self.encryption.decrypt_data(encrypted_content)
