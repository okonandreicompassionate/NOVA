import hmac
import os

from fastapi import Header, HTTPException
from supabase import Client

from storage.supabase_client import client_for_user


async def authenticated_supabase(
    authorization: str | None = Header(default=None),
    x_brain_plugin_secret: str | None = Header(default=None),
) -> tuple[str, Client]:
    """Verifies the caller is an authorized plugin (shared secret) AND a real
    Supabase user (their own JWT, checked against Supabase Auth) — then
    returns a Supabase client scoped to that user for the rest of the request.
    """
    expected_secret = os.environ.get("BRAIN_PLUGIN_SECRET")
    if not expected_secret or not x_brain_plugin_secret or not hmac.compare_digest(
        x_brain_plugin_secret, expected_secret
    ):
        raise HTTPException(status_code=403, detail="Unrecognized plugin")

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.removeprefix("Bearer ").strip()

    supabase = client_for_user(token)
    user_response = supabase.auth.get_user(token)
    if not user_response or not user_response.user:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    return user_response.user.id, supabase
