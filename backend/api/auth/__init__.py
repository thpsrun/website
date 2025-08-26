from .api_key import api_key_required
from .api_key import read_only_auth as legacy_read_only_auth

# Import auth functions from permissions module
from api.permissions import (
    public_auth,
    read_only_auth,
    contributor_auth,
    moderator_auth,
    admin_auth,
)

__all__ = [
    "public_auth",
    "read_only_auth",
    "contributor_auth",
    "moderator_auth",
    "admin_auth",
    "api_key_required",
    "legacy_read_only_auth",
]
