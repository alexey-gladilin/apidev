from apidev.core.auth_policy import (
    AUTH_MODE_BEARER,
    AUTH_MODE_PUBLIC,
    AUTH_SECURITY_BY_MODE,
    SUPPORTED_AUTH_MODES,
    SUPPORTED_AUTH_MODES_DISPLAY,
    canonicalize_auth_mode,
    normalize_auth_mode,
)


def test_auth_policy_exposes_canonical_modes_and_display() -> None:
    assert AUTH_MODE_PUBLIC == "public"
    assert AUTH_MODE_BEARER == "bearer"
    assert SUPPORTED_AUTH_MODES == (AUTH_MODE_PUBLIC, AUTH_MODE_BEARER)
    assert SUPPORTED_AUTH_MODES_DISPLAY == "bearer, public"


def test_auth_policy_normalizes_known_modes() -> None:
    assert normalize_auth_mode("  PuBlIc ") == AUTH_MODE_PUBLIC
    assert normalize_auth_mode("  BeAreR ") == AUTH_MODE_BEARER
    assert canonicalize_auth_mode("  PuBlIc ") == AUTH_MODE_PUBLIC
    assert canonicalize_auth_mode("  BeAreR ") == AUTH_MODE_BEARER


def test_auth_policy_rejects_unsupported_modes() -> None:
    try:
        canonicalize_auth_mode(" session ")
    except ValueError as exc:
        assert str(exc) == "Unsupported auth mode: session"
    else:
        raise AssertionError("Expected canonicalize_auth_mode to reject unsupported auth mode.")


def test_auth_policy_maps_openapi_security_by_mode() -> None:
    assert AUTH_SECURITY_BY_MODE[AUTH_MODE_BEARER] == [{"bearerAuth": []}]
    assert AUTH_MODE_PUBLIC not in AUTH_SECURITY_BY_MODE
