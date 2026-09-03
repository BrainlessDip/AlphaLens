"""Token encryption at rest using Fernet symmetric encryption.

If no encryption key is configured, tokens are stored plaintext
(with a warning logged). This keeps the OAuth flow decoupled from
the encryption infrastructure.
"""

import logging

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_fernet = None


def _get_fernet():
    global _fernet
    settings = get_settings()
    if _fernet is None:
        key = settings.token_encryption_key
        if key:
            from cryptography.fernet import Fernet
            _fernet = Fernet(key.encode() if isinstance(key, str) else key)
        else:
            logger.warning(
                "No TOKEN_ENCRYPTION_KEY configured. Tokens stored unencrypted. "
                "Set TOKEN_ENCRYPTION_KEY for production use."
            )
    return _fernet


def encrypt_token(plaintext: str) -> str:
    f = _get_fernet()
    if f is None:
        return plaintext
    return f.encrypt(plaintext.encode()).decode()


def decrypt_token(ciphertext: str) -> str:
    f = _get_fernet()
    if f is None:
        return ciphertext
    return f.decrypt(ciphertext.encode()).decode()
