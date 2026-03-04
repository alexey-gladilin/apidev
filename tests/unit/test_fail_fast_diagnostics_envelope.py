from __future__ import annotations

import json

from apidev.application.dto.diagnostics import FAIL_FAST_ERROR_CODES, build_envelope
from apidev.application.dto.generation_plan import GenerationDiagnostic


def test_generation_diagnostic_unified_context_is_canonical() -> None:
    diagnostic = GenerationDiagnostic(
        code="validation.PATH_BOUNDARY_VIOLATION",
        location="generator.generated_dir",
        message="generated_dir must stay inside project_dir",
        context={
            "project_dir": "/tmp/project",
            "generated_dir": "/tmp/project/.apidev/output/api",
            "unused": None,
        },
    )

    payload = diagnostic.as_unified_dict()

    assert payload["message"] == "generated_dir must stay inside project_dir"
    assert list(payload["context"].keys()) == ["generated_dir", "project_dir"]


def test_fail_fast_envelope_context_serialization_is_byte_stable() -> None:
    left = GenerationDiagnostic(
        code="validation.OUTPUT_CONTOUR_CONFLICT",
        location="generator",
        message="generator output contours overlap",
        context={
            "project_dir": "/tmp/project",
            "generated_dir": "/tmp/project/.apidev/output/api",
            "scaffold_dir": "/tmp/project/integration",
        },
    ).as_unified_dict()
    right = GenerationDiagnostic(
        code="validation.OUTPUT_CONTOUR_CONFLICT",
        location="generator",
        message="generator output contours overlap",
        context={
            "scaffold_dir": "/tmp/project/integration",
            "generated_dir": "/tmp/project/.apidev/output/api",
            "project_dir": "/tmp/project",
        },
    ).as_unified_dict()

    left_payload = build_envelope(
        command="gen",
        mode="apply",
        drift_status="error",
        diagnostics=[left],
    )
    right_payload = build_envelope(
        command="gen",
        mode="apply",
        drift_status="error",
        diagnostics=[right],
    )

    left_bytes = json.dumps(left_payload, ensure_ascii=False, separators=(",", ":"))
    right_bytes = json.dumps(right_payload, ensure_ascii=False, separators=(",", ":"))

    assert left_bytes == right_bytes


def test_fail_fast_error_code_catalog_is_stable() -> None:
    assert FAIL_FAST_ERROR_CODES == (
        "validation.PATH_BOUNDARY_VIOLATION",
        "validation.OUTPUT_CONTOUR_CONFLICT",
        "validation.INVALID_SCAFFOLD_WRITE_POLICY",
        "validation.MANUAL_TAGS_FORBIDDEN",
        "validation.RELEASE_STATE_INVALID_KEY",
        "validation.RELEASE_STATE_TYPE_MISMATCH",
        "config.INIT_PROFILE_INVALID_ENUM",
        "config.INIT_MODE_CONFLICT",
    )
