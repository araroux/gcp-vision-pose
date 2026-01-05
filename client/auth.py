# client/auth.py
import os
import shutil
import subprocess

def _find_gcloud() -> str:
    """
    Windowsでも確実に gcloud を見つける。
    - gcloud.exe / gcloud.cmd の両方を探す
    - 見つからなければ分かりやすく例外
    """
    for name in ("gcloud", "gcloud.cmd", "gcloud.exe"):
        path = shutil.which(name)
        if path:
            return path
    raise FileNotFoundError(
        "gcloud command was not found from Python. "
        "Fix: restart terminal/VSCode after installing Google Cloud SDK, "
        "or add Google Cloud SDK 'bin' to PATH."
    )

def get_id_token() -> str:
    gcloud = _find_gcloud()
    return subprocess.check_output(
        [gcloud, "auth", "print-identity-token"],
        text=True,
        stderr=subprocess.STDOUT,
    ).strip()

def auth_headers(api_url: str = None) -> dict:
    """
    Returns authentication headers for API requests.
    For localhost, no authentication is required.
    For Cloud Run, returns Bearer token with ID token.

    Args:
        api_url: The API URL to determine if authentication is needed

    Returns:
        dict: Headers dictionary (empty for localhost, with Bearer token for Cloud Run)
    """
    # Skip authentication for localhost
    if api_url and ("localhost" in api_url or "127.0.0.1" in api_url):
        return {}

    return {"Authorization": f"Bearer {get_id_token()}"}
