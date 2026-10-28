from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from app.core.config import settings
import hashlib
import logging
logger = logging.getLogger(__name__)

backend = default_backend()

def get_key(salt_name: str | None = None):
    secret = settings.ENCRYPTION_SECRET_KEY        
    """
    Derive a deterministic IV (Initialization Vector) from the salt for use in AES modes that require an IV.
    This uses the salt (or a default from settings) and the secret key to derive a 16-byte IV using SHA-256.
    """
    try:        
        if salt_name:
            salt = salt_name.encode("utf-8")
        else:
            salt = settings.ENCRYPTION_SALT.encode("utf-8")
        
        source = (secret + salt.decode("utf-8")).encode("utf-8")
        key = hashlib.sha256(source).digest()
        iv = hashlib.sha256(source).digest()[:16]
        
        return key, iv
    except Exception as e:
        logger.error(f"Error getting key: {e}")
        return None, None
    
def pad_value(value, block_size):
    try:
        padder = padding.PKCS7(block_size * 8).padder()
        padded_data = padder.update(value) + padder.finalize()
        return padded_data
    except Exception as e:
        logger.error(f"Error padding value: {e}")
        return None

def encrypt_id(id_value: str, salt_name: str | None = None) -> str | None:
    try:
        key, iv = get_key(salt_name)

        block_size = algorithms.AES.block_size // 8  # AES block size in bytes
        padded_value = pad_value(str(id_value).encode('utf-8'), block_size)

        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=backend)
        encryptor = cipher.encryptor()
        encrypted_data = encryptor.update(padded_value) + encryptor.finalize()

        # return base64.urlsafe_b64encode(encrypted_data).decode('utf-8')
        return encrypted_data.hex()   
    except Exception as e:
        logger.error(f"Error encrypting id: {e}")
        return None

def decrypt_id(encrypted_id: str, salt_name: str | None = None) -> str | None:
    try:
        key, iv = get_key(salt_name)    
        encrypted_data = bytes.fromhex(encrypted_id)

        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=backend)
        decryptor = cipher.decryptor()
        decrypted_padded_data = decryptor.update(encrypted_data) + decryptor.finalize()
        
        unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
        decrypted_data = unpadder.update(decrypted_padded_data) + unpadder.finalize()
        
        if decrypted_data.decode('utf-8') == "None":
            return None
        
        return decrypted_data.decode('utf-8')
    except Exception as e:
        logger.error(f"Error decrypting id: {e}")
        return None