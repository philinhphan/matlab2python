"""BMW LLM API authentication helpers."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone

import httpx
import requests
from openai import AsyncOpenAI

BMW_BASE_URL = "https://api.gcp.cloud.bmw/llmapi/v1"
BMW_CA_CERT_URL = "https://trustbundle.bmwgroup.net/BMW_Trusted_Certificates_Latest.pem"
BMW_CA_CERT_PATH = "BMW_Trusted_Certificates_Latest.pem"
BMW_AUTH_ENDPOINT = (
    "https://auth.bmwgroup.net/auth/oauth2/realms/root"
    "/realms/machine2machine/access_token"
)


def download_bmw_ca_cert(
    path: str = BMW_CA_CERT_PATH,
    ca_certificate_url: str = BMW_CA_CERT_URL,
) -> str:
    """Download BMW CA certificate if not already present."""
    if os.path.exists(path):
        return path
    response = requests.get(ca_certificate_url)
    response.raise_for_status()
    with open(path, "wb") as f:
        f.write(response.content)
    return path


def get_access_token(
    client_id: str,
    client_secret: str,
    auth_endpoint: str = BMW_AUTH_ENDPOINT,
) -> tuple[str, int]:
    """Obtain an OAuth access token via client_credentials flow."""
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "machine2machine",
    }
    response = requests.post(
        auth_endpoint,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data=data,
    )
    response.raise_for_status()
    payload = response.json()
    token = payload["access_token"]
    expires_in = payload.get("expires_in", 3600)
    return token, expires_in


def _is_token_valid(token: str | None, exp_str: str | None) -> bool:
    """Return True if the cached token exists and has not yet expired."""
    if not token or not exp_str:
        return False
    try:
        exp = datetime.fromisoformat(exp_str)
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) < exp
    except ValueError:
        return False


async def _sanitize_null_content(request: httpx.Request) -> None:
    """Replace null content values with empty strings in chat messages.

    BMW's LLM API gateway rejects content: null in assistant messages
    (valid per OpenAI spec for tool-call-only messages, but BMW is stricter).
    """
    if request.content:
        try:
            body = json.loads(request.content)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return
        messages = body.get("messages")
        if not messages:
            return
        changed = False
        for msg in messages:
            if msg.get("content") is None:
                msg["content"] = ""
                changed = True
        if changed:
            new_body = json.dumps(body).encode("utf-8")
            request._content = new_body
            request.headers["content-length"] = str(len(new_body))


def create_bmw_openai_client(
    api_key: str,
    client_id: str,
    client_secret: str,
    cached_token: str | None = None,
    cached_token_exp: str | None = None,
    base_url: str = BMW_BASE_URL,
    ca_cert_path: str = BMW_CA_CERT_PATH,
) -> AsyncOpenAI:
    """Build an AsyncOpenAI client configured for the BMW LLM API.

    Uses the cached access token from the environment when still valid;
    otherwise fetches a fresh token via the OAuth client-credentials flow.
    """
    if _is_token_valid(cached_token, cached_token_exp):
        access_token = cached_token
        print("Using cached BMW access token.")
    else:
        print("Fetching new BMW access token...")
        access_token, _ = get_access_token(client_id, client_secret)

    cert_path = download_bmw_ca_cert(ca_cert_path)

    return AsyncOpenAI(
        base_url=base_url,
        api_key=access_token,
        max_retries=3,
        http_client=httpx.AsyncClient(
            headers={"x-apikey": api_key},
            verify=cert_path,
            event_hooks={"request": [_sanitize_null_content]},
        ),
    )
