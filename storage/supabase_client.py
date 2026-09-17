import os

from supabase import Client, create_client

_SUPABASE_URL = os.environ["SUPABASE_URL"]
_SUPABASE_ANON_KEY = os.environ["SUPABASE_ANON_KEY"]


def client_for_user(access_token: str) -> Client:
    """A Supabase client scoped to one user's JWT.

    Never a service-role client: every query this brain makes goes through
    Postgres RLS as the calling user, exactly as it would from the Next.js
    app. The brain gains no privilege the user didn't already have.
    """
    client = create_client(_SUPABASE_URL, _SUPABASE_ANON_KEY)
    client.postgrest.auth(access_token)
    return client
