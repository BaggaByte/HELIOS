import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from helios.config import get_settings

settings = get_settings()

class EncryptionManager:
    def __init__(self):
        # We use a master key from environment, or generate a deterministic one for dev
        secret = os.environ.get("HELIOS_MASTER_KEY", "helios-dev-master-key-very-secret")
        # Salt should ideally be random per installation and stored, but fixed for dev
        salt = b"helios-salt-123"
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(secret.encode()))
        self.fernet = Fernet(key)
        
    def encrypt_data(self, data: bytes) -> bytes:
        return self.fernet.encrypt(data)
        
    def decrypt_data(self, encrypted_data: bytes) -> bytes:
        return self.fernet.decrypt(encrypted_data)
