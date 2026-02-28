from apidev.core.rules.compatibility import (
    CompatibilityCategory,
    CompatibilityChange,
    CompatibilityReport,
    classify_change,
    classify_changes,
)


def test_classify_change_uses_taxonomy() -> None:
    assert classify_change("operation-added") == CompatibilityCategory.NON_BREAKING
    assert classify_change("response-required-field-removed") == CompatibilityCategory.BREAKING
    assert classify_change("request-optional-field-added") == CompatibilityCategory.POTENTIALLY_BREAKING


def test_classify_change_unknown_code_defaults_to_potentially_breaking() -> None:
    assert classify_change("unknown-change-code") == CompatibilityCategory.POTENTIALLY_BREAKING


def test_classify_change_supports_deprecation_window_codes() -> None:
    assert classify_change("deprecation-window-violation") == CompatibilityCategory.BREAKING
    assert classify_change("deprecation-window-satisfied") == CompatibilityCategory.NON_BREAKING
    assert classify_change("baseline-ref-applied") == CompatibilityCategory.NON_BREAKING
    assert classify_change("baseline-missing") == CompatibilityCategory.BREAKING
    assert classify_change("baseline-invalid") == CompatibilityCategory.BREAKING


def test_classify_changes_returns_deterministic_report_order_and_counts() -> None:
    changes = [
        CompatibilityChange(code="request-optional-field-added", location="b/op"),
        CompatibilityChange(code="operation-added", location="a/op"),
        CompatibilityChange(code="response-required-field-removed", location="c/op"),
        CompatibilityChange(code="operation-added", location="d/op"),
    ]

    report = classify_changes(changes)

    assert isinstance(report, CompatibilityReport)
    assert report.overall == CompatibilityCategory.BREAKING
    assert report.counts == {
        CompatibilityCategory.NON_BREAKING: 2,
        CompatibilityCategory.POTENTIALLY_BREAKING: 1,
        CompatibilityCategory.BREAKING: 1,
    }
    assert [(item.category, item.code, item.location) for item in report.items] == [
        (CompatibilityCategory.BREAKING, "response-required-field-removed", "c/op"),
        (CompatibilityCategory.POTENTIALLY_BREAKING, "request-optional-field-added", "b/op"),
        (CompatibilityCategory.NON_BREAKING, "operation-added", "a/op"),
        (CompatibilityCategory.NON_BREAKING, "operation-added", "d/op"),
    ]


def test_classify_changes_is_input_order_independent() -> None:
    first = [
        CompatibilityChange(code="operation-added", location="z"),
        CompatibilityChange(code="response-required-field-removed", location="a"),
    ]
    second = list(reversed(first))

    first_report = classify_changes(first)
    second_report = classify_changes(second)

    assert first_report.overall == second_report.overall
    assert first_report.counts == second_report.counts
    assert first_report.items == second_report.items
