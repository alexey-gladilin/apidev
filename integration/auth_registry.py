"""Manual integration scaffold: resolve auth dependencies by auth mode.

Supported auth modes from generated metadata:
- public
- bearer
"""

from typing import Any


def resolve_auth_dependency(auth_mode: str) -> Any:
    if auth_mode == "public":
        return None
    if auth_mode == "bearer":
        # TODO: return your FastAPI dependency, e.g. require_bearer_user
        raise NotImplementedError("Configure bearer auth dependency.")
    raise ValueError(f"Unsupported auth mode: {auth_mode}")
