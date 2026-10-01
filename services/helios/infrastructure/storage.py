import os
import aiofiles
import uuid
from pathlib import Path
from helios.config import get_settings
from helios.infrastructure.encryption import EncryptionManager


class StorageManager:
    def __init__(self, base_dir: str = None):
        if base_dir is None:
            settings = get_settings()
            base_dir = settings.UPLOAD_DIR
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.encryption = EncryptionManager()

    async def save_file(self, content: bytes) -> str:
        """Saves a file to disk with a generated UUID name, encrypting it before writing. Returns the UUID."""
        file_id = str(uuid.uuid4())
        file_path = self.base_dir / file_id

        encrypted_content = self.encryption.encrypt_data(content)

        async with aiofiles.open(file_path, "wb") as f:
            await f.write(encrypted_content)

        return file_id

    async def load_file(self, file_id: str) -> bytes:
        """Loads and decrypts a file from disk using its UUID."""
        file_path = self.base_dir / file_id
        if not file_path.exists():
            raise FileNotFoundError(f"File {file_id} not found")

        async with aiofiles.open(file_path, "rb") as f:
            encrypted_content = await f.read()

        return self.encryption.decrypt_data(encrypted_content)

    async def delete_file(self, file_id: str) -> None:
        """Deletes a file from disk."""
        file_path = self.base_dir / file_id
        if file_path.exists():
            try:
                os.remove(file_path)
            except OSError as e:
                import logging

                logging.getLogger(__name__).warning(
                    f"Could not delete storage file {file_id}: {e}"
                )
