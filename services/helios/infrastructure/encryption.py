import base64
import logging
import os
from pathlib import Path

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from helios.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()


class EncryptionManager:
    def __init__(self):
        key_dir = Path(settings.ENCRYPTION_KEY_PATH)
        key_file = key_dir / "master.key"

        # If it's missing, we fail closed by raising an exception, unless we explicitly provision it.
        if not key_file.exists():
            storage_dir = Path(settings.UPLOAD_DIR)
            legacy_storage_dir = Path(".helios_storage")

            # Check if this is an upgrade from an older version
            is_upgrade = (storage_dir.exists() and any(storage_dir.rglob("*"))) or (
                legacy_storage_dir.exists() and any(legacy_storage_dir.rglob("*"))
            )

            # Generate a fresh secure key
            key_dir.mkdir(parents=True, exist_ok=True)
            secret = os.urandom(32)
            salt = os.urandom(16)
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=480000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(secret))
            with open(key_file, "wb") as f:
                f.write(salt + b"\n" + key)
            self._secure_file(key_file)

            # If there's existing data, we must migrate it to the fresh key
            if is_upgrade:
                self._migrate_existing_files(key)

        with open(key_file, "rb") as f:
            data = f.read().split(b"\n")
            if len(data) != 2:
                raise ValueError("Corrupted master key file")
            salt, key = data[0], data[1]

        self.fernet = Fernet(key)

    def _migrate_existing_files(self, fresh_key: bytes):
        """Migrates legacy plaintext and legacy-encrypted files to the new fresh key with atomic backups."""
        marker_file = Path(settings.UPLOAD_DIR) / ".migration_complete"
        if marker_file.exists():
            return

        legacy_secret = b"helios-dev-master-key-very-secret"
        legacy_salt = b"helios-salt-123"
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=legacy_salt,
            iterations=480000,
        )
        legacy_key = base64.urlsafe_b64encode(kdf.derive(legacy_secret))
        legacy_fernet = Fernet(legacy_key)
        fresh_fernet = Fernet(fresh_key)

        directories_to_migrate = [Path(settings.UPLOAD_DIR), Path(".helios_storage")]

        for d in directories_to_migrate:
            if not d.exists():
                continue
            for file_path in d.rglob("*"):
                if (
                    not file_path.is_file()
                    or file_path.name.endswith(".bak")
                    or file_path.name == ".migration_complete"
                ):
                    continue

                with open(file_path, "rb") as f:
                    content = f.read()

                if not content:
                    continue

                # Fernet tokens start with gAAAAA
                if content.startswith(b"gAAAAA"):
                    try:
                        plaintext = legacy_fernet.decrypt(content)
                    except Exception:
                        raise ValueError(
                            f"Encryption key lost. Cannot decrypt {file_path}. Halting to prevent data loss."
                        )
                else:
                    # It's a legacy plaintext file
                    plaintext = content

                # Re-encrypt with fresh key
                encrypted = fresh_fernet.encrypt(plaintext)

                # Write to backup, write new file, then delete backup
                bak_path = file_path.with_suffix(file_path.suffix + ".bak")
                import shutil

                shutil.copy2(file_path, bak_path)

                with open(file_path, "wb") as f:
                    f.write(encrypted)

                bak_path.unlink(missing_ok=True)

        # Write marker to prevent re-running
        marker_file.parent.mkdir(parents=True, exist_ok=True)
        marker_file.touch()
        logger.info("Successfully migrated existing files to the fresh encryption key.")

    def _secure_file(self, path: Path):
        """Apply OS-specific restrictive permissions."""
        if os.name == "posix":
            os.chmod(path, 0o600)
        elif os.name == "nt":
            import subprocess

            username = os.environ.get("USERNAME")
            if username:
                subprocess.run(
                    ["icacls", str(path), "/inheritance:r"], capture_output=True
                )
                subprocess.run(
                    ["icacls", str(path), "/grant", f"{username}:F"],
                    capture_output=True,
                )

    def encrypt_data(self, data: bytes) -> bytes:
        return self.fernet.encrypt(data)

    def decrypt_data(self, encrypted_data: bytes) -> bytes:
        return self.fernet.decrypt(encrypted_data)
