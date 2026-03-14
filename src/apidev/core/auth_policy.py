from typing import Literal, cast

AuthMode = Literal["public", "bearer"]

AUTH_MODE_PUBLIC: AuthMode = "public"
AUTH_MODE_BEARER: AuthMode = "bearer"
DEFAULT_AUTH_MODE: AuthMode = AUTH_MODE_PUBLIC

SUPPORTED_AUTH_MODES: tuple[AuthMode, ...] = (
    AUTH_MODE_PUBLIC,
    AUTH_MODE_BEARER,
)
SUPPORTED_AUTH_MODES_SET = frozenset(SUPPORTED_AUTH_MODES)
SUPPORTED_AUTH_MODES_DISPLAY = ", ".join(sorted(SUPPORTED_AUTH_MODES))

AUTH_SECURITY_BY_MODE: dict[AuthMode, list[dict[str, list[str]]]] = {
    AUTH_MODE_BEARER: [{"bearerAuth": []}],
}


def normalize_auth_mode(raw_auth_mode: object) -> str:
    return str(raw_auth_mode).strip().lower()


def canonicalize_auth_mode(raw_auth_mode: object) -> AuthMode:
    normalized_auth_mode = normalize_auth_mode(raw_auth_mode)
    if normalized_auth_mode not in SUPPORTED_AUTH_MODES_SET:
        raise ValueError(f"Unsupported auth mode: {normalized_auth_mode}")
    return cast(AuthMode, normalized_auth_mode)
