import hmac
import os

import jwt
from fastapi import Header, HTTPException
from jwt import PyJWKClient
from supabase import Client

from storage.supabase_client import client_for_user

# Verifying a JWT against Supabase's Auth API is a network round-trip on
# every single message — the single biggest fixed cost in the request path.
# This project's JWTs are ES256-signed against a JWKS Supabase publishes, so
# we can verify the signature locally instead. PyJWKClient caches the keyset
# in-process, so after the first request this is pure CPU, no network call.
_jwks_client = PyJWKClient(f"{os.environ['SUPABASE_URL']}/auth/v1/.well-known/jwks.json")


async def authenticated_supabase(
    authorization: str | None = Header(default=None),
    x_brain_plugin_secret: str | None = Header(default=None),
) -> tuple[str, Client]:
    """Verifies the caller is an authorized plugin (shared secret) AND a real
    Supabase user (their own JWT, verified locally against Supabase's published
    signing keys) — then returns a Supabase client scoped to that user.
    """
    expected_secret = os.environ.get("BRAIN_PLUGIN_SECRET")
    if not expected_secret or not x_brain_plugin_secret or not hmac.compare_digest(
        x_brain_plugin_secret, expected_secret
    ):
        raise HTTPException(status_code=403, detail="Unrecognized plugin")

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.removeprefix("Bearer ").strip()

    try:
        signing_key = _jwks_client.get_signing_key_from_jwt(token)
        payload = jwt.decode(token, signing_key.key, algorithms=["ES256"], audience="authenticated")
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid or expired session: {e}")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Token missing subject")

    supabase = client_for_user(token)
    return user_id, supabase
