import json
from pathlib import Path

from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials

from app.core.config import settings

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

# Almacena el code_verifier entre get_auth_url y exchange_code (mismo proceso)
_pending_verifiers: dict[int, str] = {}


def _client_config() -> dict:
    return {
        "web": {
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [f"{settings.base_url}/oauth/callback"],
        }
    }


def _credentials_path(channel_id: int) -> Path:
    return Path(settings.credentials_dir) / f"channel_{channel_id}.json"


def get_auth_url(channel_id: int) -> str:
    flow = Flow.from_client_config(
        _client_config(),
        scopes=SCOPES,
        redirect_uri=f"{settings.base_url}/oauth/callback",
    )
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        state=str(channel_id),
        prompt="consent",
    )
    # Persiste el code_verifier si la librería usó PKCE automáticamente
    verifier = getattr(flow, "code_verifier", None)
    if verifier:
        _pending_verifiers[channel_id] = verifier
    return auth_url


def exchange_code(channel_id: int, code: str) -> None:
    flow = Flow.from_client_config(
        _client_config(),
        scopes=SCOPES,
        redirect_uri=f"{settings.base_url}/oauth/callback",
        state=str(channel_id),
    )
    verifier = _pending_verifiers.pop(channel_id, None)
    flow.fetch_token(code=code, code_verifier=verifier)
    creds = flow.credentials

    cred_path = _credentials_path(channel_id)
    cred_path.parent.mkdir(parents=True, exist_ok=True)
    cred_path.write_text(json.dumps({
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": list(creds.scopes or SCOPES),
    }))


def load_credentials(channel_id: int) -> Credentials | None:
    cred_path = _credentials_path(channel_id)
    if not cred_path.exists():
        return None
    data = json.loads(cred_path.read_text())
    return Credentials(
        token=data["token"],
        refresh_token=data["refresh_token"],
        token_uri=data["token_uri"],
        client_id=data["client_id"],
        client_secret=data["client_secret"],
        scopes=data["scopes"],
    )


def has_credentials(channel_id: int) -> bool:
    return _credentials_path(channel_id).exists()
