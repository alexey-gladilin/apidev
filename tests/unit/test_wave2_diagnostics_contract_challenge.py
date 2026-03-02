from apidev.commands.common.compatibility import (
    build_compatibility_payload,
    compatibility_diagnostics_unified,
)


class _CompatibilityEntry:
    def __init__(self, category: str, code: str, location: str, detail: str = "") -> None:
        self.category = category
        self.code = code
        self.location = location
        self.detail = detail


class _CompatibilityPayload:
    def __init__(self, diagnostics: object, counts: object = None, overall: str = "non-breaking") -> None:
        self.diagnostics = diagnostics
        self.counts = counts
        self.overall = overall


def test_compatibility_payload_tolerates_none_inputs() -> None:
    compatibility = _CompatibilityPayload(diagnostics=None, counts=None, overall="non-breaking")

    diagnostics = compatibility_diagnostics_unified(compatibility=compatibility, source="diff-service")
    payload = build_compatibility_payload(
        policy="warn",
        compatibility=compatibility,
        source="diff-service",
    )

    assert diagnostics == []
    assert payload["diagnostics"] == []
    assert payload["counts"] == {
        "non-breaking": 0,
        "potentially-breaking": 0,
        "breaking": 0,
    }


def test_compatibility_diagnostics_ordering_is_deterministic_for_boundary_categories() -> None:
    compatibility = _CompatibilityPayload(
        diagnostics=[
            _CompatibilityEntry(
                category="unexpected-category",
                code="compatibility.zzz",
                location="operation:c",
                detail="3",
            ),
            _CompatibilityEntry(
                category="breaking",
                code="compatibility.aaa",
                location="operation:a",
                detail="1",
            ),
            _CompatibilityEntry(
                category="potentially-breaking",
                code="compatibility.bbb",
                location="operation:b",
                detail="2",
            ),
        ],
        counts={"breaking": 1, "potentially-breaking": 1, "non-breaking": 1},
        overall="breaking",
    )

    diagnostics = compatibility_diagnostics_unified(compatibility=compatibility, source="diff-service")
    assert [item["code"] for item in diagnostics] == [
        "compatibility.aaa",
        "compatibility.bbb",
        "compatibility.zzz",
    ]
    assert [item["severity"] for item in diagnostics] == ["error", "warning", "info"]
