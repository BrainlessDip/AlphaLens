import base64
import hashlib
import secrets
import time
from dataclasses import dataclass


STATE_TTL_SECONDS = 600


@dataclass(frozen=True)
class PKCEValues:
    code_verifier: str
    code_challenge: str


@dataclass(frozen=True)
class OAuthState:
    state: str
    code_verifier: str
    code_challenge: str
    created_at: float

    @property
    def is_expired(self) -> bool:
        return (time.time() - self.created_at) > STATE_TTL_SECONDS


def generate_state() -> str:
    return secrets.token_urlsafe(32)


def generate_pkce() -> PKCEValues:
    code_verifier = secrets.token_urlsafe(32)
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    code_challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return PKCEValues(code_verifier=code_verifier, code_challenge=code_challenge)


def create_oauth_state() -> OAuthState:
    pkce = generate_pkce()
    return OAuthState(
        state=generate_state(),
        code_verifier=pkce.code_verifier,
        code_challenge=pkce.code_challenge,
        created_at=time.time(),
    )
