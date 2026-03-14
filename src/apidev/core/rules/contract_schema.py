from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from apidev.core.auth_policy import (
    SUPPORTED_AUTH_MODES_DISPLAY,
    SUPPORTED_AUTH_MODES_SET,
    canonicalize_auth_mode,
    normalize_auth_mode,
)
from apidev.core.models.contract import (
    ACCESS_PATTERN_FIELD,
    collect_operation_metadata_empty_value_errors,
    EndpointContract,
    OPERATION_METADATA_FIELDS,
    OPERATION_INTENT_FIELD,
    RefSchemaNodeModel,
    SharedModelContractModel,
    normalize_operation_metadata_value,
)
from apidev.core.models.contract_document import ContractDocument
from apidev.core.models.diagnostic import ValidationDiagnostic

SCHEMA_INVALID_YAML = "SCHEMA_INVALID_YAML"
SCHEMA_ROOT_NOT_MAPPING = "SCHEMA_ROOT_NOT_MAPPING"
SCHEMA_MISSING_FIELD = "SCHEMA_MISSING_FIELD"
SCHEMA_INVALID_TYPE = "SCHEMA_INVALID_TYPE"
SCHEMA_INVALID_VALUE = "SCHEMA_INVALID_VALUE"
SCHEMA_UNKNOWN_FIELD = "SCHEMA_UNKNOWN_FIELD"
REQUEST_UNKNOWN_FIELD = "validation.request-unknown-field"
REQUEST_PATH_MISMATCH = "validation.request-path-mismatch"
MISSING_REQUEST_PATH = "validation.missing-request-path"
DUPLICATE_PATH_PLACEHOLDER = "validation.duplicate-path-placeholder"

RULE_PARSE = "schema.yaml.parse"
RULE_ROOT_SHAPE = "schema.contract.root"
RULE_REQUIRED_FIELD = "schema.contract.required_field"
RULE_FIELD_TYPE = "schema.contract.field_type"
RULE_FIELD_VALUE = "schema.contract.field_value"
RULE_FIELD_UNKNOWN = "schema.contract.unknown_field"
JSON_SCHEMA_TYPES = {"object", "array", "string", "integer", "number", "boolean", "null"}
HTTP_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}
ROOT_ALLOWED_FIELDS = {
    "contract_type",
    "method",
    "path",
    "auth",
    "summary",
    "description",
    "local_models",
    "request",
    "response",
    "errors",
}.union(OPERATION_METADATA_FIELDS)
SHARED_ROOT_ALLOWED_FIELDS = {"contract_type", "name", "description", "model"}
REQUEST_ALLOWED_FIELDS = {"path", "query", "body"}
RESPONSE_ALLOWED_FIELDS = {"status", "body"}
ERROR_ALLOWED_FIELDS = {"code", "http_status", "body", "example"}
SCHEMA_ALLOWED_FIELDS = {
    "$ref",
    "type",
    "properties",
    "items",
    "required",
    "description",
    "enum",
    "example",
}
PATH_SAFE_PATTERN = re.compile(r"^/[A-Za-z0-9\-._~/%{}:]*$")
PATH_PLACEHOLDER_PATTERN = re.compile(r"\{([^{}]+)\}")


def validate_contract_schema(
    document: ContractDocument,
) -> tuple[EndpointContract | None, list[ValidationDiagnostic]]:
    diagnostics: list[ValidationDiagnostic] = []
    relpath = _location(document.contract_relpath)

    if document.parse_error:
        diagnostics.append(
            ValidationDiagnostic(
                code=SCHEMA_INVALID_YAML,
                severity="error",
                message=f"Invalid YAML: {document.parse_error}",
                location=relpath,
                rule=RULE_PARSE,
            )
        )
        return None, diagnostics

    data = document.data
    if not isinstance(data, dict):
        diagnostics.append(
            ValidationDiagnostic(
                code=SCHEMA_ROOT_NOT_MAPPING,
                severity="error",
                message="Contract root must be a mapping object.",
                location=relpath,
                rule=RULE_ROOT_SHAPE,
            )
        )
        return None, diagnostics

    contract_type = data.get("contract_type")
    diagnostics.extend(_require_type(relpath, "contract_type", contract_type, str))
    if isinstance(contract_type, str):
        normalized_contract_type = contract_type.strip().lower()
        if normalized_contract_type == "shared_model":
            return _validate_shared_model_contract(document, data)
        if normalized_contract_type != "operation":
            diagnostics.append(
                ValidationDiagnostic(
                    code=SCHEMA_INVALID_VALUE,
                    severity="error",
                    message="Field 'contract_type' must be either 'operation' or 'shared_model'.",
                    location=f"{relpath}:contract_type",
                    rule=RULE_FIELD_VALUE,
                )
            )

    required_fields = (
        "method",
        "path",
        "auth",
        "description",
        "response",
        "errors",
        OPERATION_INTENT_FIELD,
        ACCESS_PATTERN_FIELD,
    )
    for field_name in required_fields:
        if field_name not in data or data[field_name] is None:
            diagnostics.append(
                ValidationDiagnostic(
                    code=SCHEMA_MISSING_FIELD,
                    severity="error",
                    message=f"Missing required field '{field_name}'.",
                    location=f"{relpath}:{field_name}",
                    rule=RULE_REQUIRED_FIELD,
                )
            )
    diagnostics.extend(_report_unknown_fields(relpath, "contract", data, ROOT_ALLOWED_FIELDS))

    method = data.get("method")
    path = data.get("path")
    auth = data.get("auth")
    summary = data.get("summary")
    description = data.get("description")
    response = data.get("response")
    request = data.get("request")
    errors = data.get("errors")
    local_models = data.get("local_models")
    intent = data.get(OPERATION_INTENT_FIELD)
    access_pattern = data.get(ACCESS_PATTERN_FIELD)

    diagnostics.extend(_require_type(relpath, "method", method, str))
    diagnostics.extend(_require_type(relpath, "path", path, str))
    diagnostics.extend(_require_type(relpath, "auth", auth, str))
    diagnostics.extend(_require_type(relpath, "summary", summary, str))
    diagnostics.extend(_require_type(relpath, "description", description, str))
    diagnostics.extend(_require_type(relpath, OPERATION_INTENT_FIELD, intent, str))
    diagnostics.extend(_require_type(relpath, ACCESS_PATTERN_FIELD, access_pattern, str))
    diagnostics.extend(_require_type(relpath, "request", request, dict))
    diagnostics.extend(_require_type(relpath, "response", response, dict))
    diagnostics.extend(_require_type(relpath, "errors", errors, list))
    diagnostics.extend(_require_type(relpath, "local_models", local_models, dict))

    if isinstance(method, str) and not method.strip():
        diagnostics.append(
            ValidationDiagnostic(
                code=SCHEMA_INVALID_VALUE,
                severity="error",
                message="Field 'method' must be non-empty.",
                location=f"{relpath}:method",
                rule=RULE_FIELD_VALUE,
            )
        )
    elif isinstance(method, str):
        normalized_method = method.strip().upper()
        if normalized_method not in HTTP_METHODS:
            diagnostics.append(
                ValidationDiagnostic(
                    code=SCHEMA_INVALID_VALUE,
                    severity="error",
                    message=(f"Field 'method' must be one of: {', '.join(sorted(HTTP_METHODS))}."),
                    location=f"{relpath}:method",
                    rule=RULE_FIELD_VALUE,
                )
            )

    if isinstance(path, str) and not path.startswith("/"):
        diagnostics.append(
            ValidationDiagnostic(
                code=SCHEMA_INVALID_VALUE,
                severity="error",
                message="Field 'path' must start with '/'.",
                location=f"{relpath}:path",
                rule=RULE_FIELD_VALUE,
            )
        )
    elif isinstance(path, str):
        if " " in path:
            diagnostics.append(
                ValidationDiagnostic(
                    code=SCHEMA_INVALID_VALUE,
                    severity="error",
                    message="Field 'path' must not contain spaces.",
                    location=f"{relpath}:path",
                    rule=RULE_FIELD_VALUE,
                )
            )
        if not path.strip():
            diagnostics.append(
                ValidationDiagnostic(
                    code=SCHEMA_INVALID_VALUE,
                    severity="error",
                    message="Field 'path' must be non-empty.",
                    location=f"{relpath}:path",
                    rule=RULE_FIELD_VALUE,
                )
            )
        if any(char in path for char in ('"', "'", "\\", "\n", "\r", "\t")):
            diagnostics.append(
                ValidationDiagnostic(
                    code=SCHEMA_INVALID_VALUE,
                    severity="error",
                    message=(
                        "Field 'path' contains unsupported characters for code generation safety."
                    ),
                    location=f"{relpath}:path",
                    rule=RULE_FIELD_VALUE,
                )
            )
        if not PATH_SAFE_PATTERN.fullmatch(path):
            diagnostics.append(
                ValidationDiagnostic(
                    code=SCHEMA_INVALID_VALUE,
                    severity="error",
                    message=(
                        "Field 'path' must contain only URL-safe characters and parameter braces."
                    ),
                    location=f"{relpath}:path",
                    rule=RULE_FIELD_VALUE,
                )
            )

    if isinstance(auth, str):
        normalized_auth = normalize_auth_mode(auth)
        if normalized_auth not in SUPPORTED_AUTH_MODES_SET:
            diagnostics.append(
                ValidationDiagnostic(
                    code=SCHEMA_INVALID_VALUE,
                    severity="error",
                    message=f"Field 'auth' must be one of: {SUPPORTED_AUTH_MODES_DISPLAY}.",
                    location=f"{relpath}:auth",
                    rule=RULE_FIELD_VALUE,
                )
            )

    if isinstance(description, str) and not description.strip():
        diagnostics.append(
            ValidationDiagnostic(
                code=SCHEMA_INVALID_VALUE,
                severity="error",
                message="Field 'description' must be non-empty.",
                location=f"{relpath}:description",
                rule=RULE_FIELD_VALUE,
            )
        )

    diagnostics.extend(_validate_operation_metadata(relpath, intent, access_pattern))

    request_has_unknown_fields = False
    request_path_fragment: Any = None
    if isinstance(request, dict):
        request_unknown_fields = _report_unknown_fields(
            relpath,
            "request",
            request,
            REQUEST_ALLOWED_FIELDS,
            diagnostic_code=REQUEST_UNKNOWN_FIELD,
        )
        request_has_unknown_fields = bool(request_unknown_fields)
        diagnostics.extend(request_unknown_fields)
        if not request_unknown_fields:
            for request_fragment in sorted(REQUEST_ALLOWED_FIELDS):
                request_payload = request.get(request_fragment)
                diagnostics.extend(
                    _require_type(relpath, f"request.{request_fragment}", request_payload, dict)
                )
                if isinstance(request_payload, dict):
                    diagnostics.extend(
                        _validate_body_schema(
                            relpath,
                            f"request.{request_fragment}",
                            request_payload,
                            unknown_field_code=REQUEST_UNKNOWN_FIELD,
                        )
                    )
        request_path_fragment = request.get("path")

    diagnostics.extend(
        _validate_request_path_consistency(
            relpath=relpath,
            route_path=path,
            request=request,
            request_path_fragment=request_path_fragment,
            skip_checks=request_has_unknown_fields,
        )
    )

    response_status: Any = None
    response_body: Any = None
    if isinstance(response, dict):
        diagnostics.extend(
            _report_unknown_fields(relpath, "response", response, RESPONSE_ALLOWED_FIELDS)
        )
        if "status" not in response:
            diagnostics.append(
                ValidationDiagnostic(
                    code=SCHEMA_MISSING_FIELD,
                    severity="error",
                    message="Missing required field 'response.status'.",
                    location=f"{relpath}:response.status",
                    rule=RULE_REQUIRED_FIELD,
                )
            )
        if "body" not in response:
            diagnostics.append(
                ValidationDiagnostic(
                    code=SCHEMA_MISSING_FIELD,
                    severity="error",
                    message="Missing required field 'response.body'.",
                    location=f"{relpath}:response.body",
                    rule=RULE_REQUIRED_FIELD,
                )
            )

        response_status = response.get("status")
        response_body = response.get("body")
        diagnostics.extend(_require_type(relpath, "response.status", response_status, int))
        diagnostics.extend(_require_type(relpath, "response.body", response_body, dict))
        if isinstance(response_status, int) and not (100 <= response_status <= 599):
            diagnostics.append(
                ValidationDiagnostic(
                    code=SCHEMA_INVALID_VALUE,
                    severity="error",
                    message="Field 'response.status' must be within HTTP range 100..599.",
                    location=f"{relpath}:response.status",
                    rule=RULE_FIELD_VALUE,
                )
            )
        if isinstance(response_body, dict):
            diagnostics.extend(_validate_body_schema(relpath, "response.body", response_body))

    if isinstance(errors, list):
        seen_error_codes: set[str] = set()
        normalized_errors: list[dict[str, Any]] = []
        for index, error_item in enumerate(errors):
            prefix = f"errors[{index}]"
            diagnostics.extend(_require_type(relpath, prefix, error_item, dict))
            if not isinstance(error_item, dict):
                continue

            normalized_error_item = _normalize_error_example(
                relpath=relpath,
                prefix=prefix,
                error_item=error_item,
                diagnostics=diagnostics,
            )
            diagnostics.extend(
                _report_unknown_fields(relpath, prefix, normalized_error_item, ERROR_ALLOWED_FIELDS)
            )
            diagnostics.extend(
                _require_type(relpath, f"{prefix}.code", normalized_error_item.get("code"), str)
            )
            diagnostics.extend(
                _require_type(
                    relpath, f"{prefix}.http_status", normalized_error_item.get("http_status"), int
                )
            )
            diagnostics.extend(
                _require_type(relpath, f"{prefix}.body", normalized_error_item.get("body"), dict)
            )
            code = normalized_error_item.get("code")
            if isinstance(code, str):
                normalized_code = code.strip()
                if not normalized_code:
                    diagnostics.append(
                        ValidationDiagnostic(
                            code=SCHEMA_INVALID_VALUE,
                            severity="error",
                            message=f"Field '{prefix}.code' must be non-empty.",
                            location=f"{relpath}:{prefix}.code",
                            rule=RULE_FIELD_VALUE,
                        )
                    )
                elif not all(ch.isupper() or ch.isdigit() or ch == "_" for ch in normalized_code):
                    diagnostics.append(
                        ValidationDiagnostic(
                            code=SCHEMA_INVALID_VALUE,
                            severity="error",
                            message=(f"Field '{prefix}.code' must use UPPER_SNAKE_CASE format."),
                            location=f"{relpath}:{prefix}.code",
                            rule=RULE_FIELD_VALUE,
                        )
                    )
                if normalized_code in seen_error_codes:
                    diagnostics.append(
                        ValidationDiagnostic(
                            code=SCHEMA_INVALID_VALUE,
                            severity="error",
                            message=f"Duplicate error code '{normalized_code}' in errors list.",
                            location=f"{relpath}:{prefix}.code",
                            rule=RULE_FIELD_VALUE,
                        )
                    )
                seen_error_codes.add(normalized_code)

            http_status = normalized_error_item.get("http_status")
            if isinstance(http_status, int) and not (400 <= http_status <= 599):
                diagnostics.append(
                    ValidationDiagnostic(
                        code=SCHEMA_INVALID_VALUE,
                        severity="error",
                        message=f"Field '{prefix}.http_status' must be within 400..599.",
                        location=f"{relpath}:{prefix}.http_status",
                        rule=RULE_FIELD_VALUE,
                    )
                )
            body = normalized_error_item.get("body")
            if isinstance(body, dict):
                diagnostics.extend(_validate_body_schema(relpath, f"{prefix}.body", body))
            normalized_errors.append(normalized_error_item)
    else:
        normalized_errors = []

    normalized_local_models: dict[str, dict[str, Any]] = {}
    if isinstance(local_models, dict):
        for model_name, model_schema in sorted(local_models.items()):
            prefix = f"local_models.{model_name}"
            diagnostics.extend(_require_type(relpath, prefix, model_schema, dict))
            if isinstance(model_name, str) and not model_name.strip():
                diagnostics.append(
                    ValidationDiagnostic(
                        code=SCHEMA_INVALID_VALUE,
                        severity="error",
                        message="Field 'local_models' contains an empty model name.",
                        location=f"{relpath}:local_models",
                        rule=RULE_FIELD_VALUE,
                    )
                )
            if not isinstance(model_schema, dict):
                continue
            diagnostics.extend(_validate_body_schema(relpath, prefix, model_schema))
            normalized_local_models[model_name] = dict(model_schema)

    if diagnostics:
        return None, diagnostics

    request_path_schema = request.get("path") if isinstance(request, dict) else {}
    request_query_schema = request.get("query") if isinstance(request, dict) else {}
    request_body_schema = request.get("body") if isinstance(request, dict) else {}

    return (
        EndpointContract(
            source_path=document.source_path,
            method=str(method).strip().upper(),
            path=str(path).strip(),
            auth=canonicalize_auth_mode(auth),
            description=str(description).strip(),
            response_status=int(response_status),
            response_body=dict(response_body),
            errors=normalized_errors,
            intent=normalize_operation_metadata_value(intent),
            access_pattern=normalize_operation_metadata_value(access_pattern),
            request_path=dict(request_path_schema) if isinstance(request_path_schema, dict) else {},
            request_query=(
                dict(request_query_schema) if isinstance(request_query_schema, dict) else {}
            ),
            request_body=dict(request_body_schema) if isinstance(request_body_schema, dict) else {},
            local_models=normalized_local_models,
        ),
        diagnostics,
    )


def _require_type(
    relpath: str, field_name: str, value: Any, expected_type: type[Any]
) -> list[ValidationDiagnostic]:
    if value is None or isinstance(value, expected_type):
        return []
    return [
        ValidationDiagnostic(
            code=SCHEMA_INVALID_TYPE,
            severity="error",
            message=(
                f"Field '{field_name}' must be of type "
                f"{_type_name(expected_type)}, got {type(value).__name__}."
            ),
            location=f"{relpath}:{field_name}",
            rule=RULE_FIELD_TYPE,
        )
    ]


def _validate_operation_metadata(
    relpath: str, intent: Any, access_pattern: Any
) -> list[ValidationDiagnostic]:
    return [
        ValidationDiagnostic(
            code=SCHEMA_INVALID_VALUE,
            severity="error",
            message=message,
            location=f"{relpath}:{field_name}",
            rule=RULE_FIELD_VALUE,
        )
        for field_name, message in collect_operation_metadata_empty_value_errors(
            intent=intent,
            access_pattern=access_pattern,
        ).items()
    ]


def _validate_body_schema(
    relpath: str,
    field_name: str,
    schema_fragment: dict[str, Any],
    *,
    unknown_field_code: str = SCHEMA_UNKNOWN_FIELD,
) -> list[ValidationDiagnostic]:
    diagnostics: list[ValidationDiagnostic] = []
    diagnostics.extend(
        _report_unknown_fields(
            relpath,
            field_name,
            schema_fragment,
            SCHEMA_ALLOWED_FIELDS,
            diagnostic_code=unknown_field_code,
        )
    )

    if "$ref" in schema_fragment:
        diagnostics.extend(_validate_ref_schema_node(relpath, field_name, schema_fragment))
        return diagnostics

    declared_type = schema_fragment.get("type")
    if declared_type is not None:
        if not isinstance(declared_type, str):
            diagnostics.extend(_require_type(relpath, f"{field_name}.type", declared_type, str))
        elif declared_type not in JSON_SCHEMA_TYPES:
            diagnostics.append(
                ValidationDiagnostic(
                    code=SCHEMA_INVALID_VALUE,
                    severity="error",
                    message=(
                        f"Field '{field_name}.type' must be one of: "
                        f"{', '.join(sorted(JSON_SCHEMA_TYPES))}."
                    ),
                    location=f"{relpath}:{field_name}.type",
                    rule=RULE_FIELD_VALUE,
                )
            )
    else:
        diagnostics.append(
            ValidationDiagnostic(
                code=SCHEMA_MISSING_FIELD,
                severity="error",
                message=f"Missing required field '{field_name}.type'.",
                location=f"{relpath}:{field_name}.type",
                rule=RULE_REQUIRED_FIELD,
            )
        )

    properties = schema_fragment.get("properties")
    if properties is not None:
        diagnostics.extend(_require_type(relpath, f"{field_name}.properties", properties, dict))
        if isinstance(properties, dict):
            for prop_name, prop_schema in sorted(properties.items()):
                prop_field_name = f"{field_name}.properties.{prop_name}"
                if isinstance(prop_schema, str):
                    diagnostics.extend(
                        _validate_shorthand_ref(relpath, prop_field_name, prop_schema)
                    )
                else:
                    diagnostics.extend(_require_type(relpath, prop_field_name, prop_schema, dict))
                if isinstance(prop_schema, dict):
                    diagnostics.extend(_validate_body_schema(relpath, prop_field_name, prop_schema))
                required_value = (
                    prop_schema.get("required") if isinstance(prop_schema, dict) else None
                )
                if required_value is not None:
                    diagnostics.extend(
                        _require_type(relpath, f"{prop_field_name}.required", required_value, bool)
                    )
                if isinstance(prop_name, str) and not prop_name.strip():
                    diagnostics.append(
                        ValidationDiagnostic(
                            code=SCHEMA_INVALID_VALUE,
                            severity="error",
                            message=f"Property name at '{field_name}.properties' must be non-empty.",
                            location=f"{relpath}:{field_name}.properties",
                            rule=RULE_FIELD_VALUE,
                        )
                    )

    items = schema_fragment.get("items")
    if items is not None:
        if isinstance(items, str):
            diagnostics.extend(_validate_shorthand_ref(relpath, f"{field_name}.items", items))
            items = None
        else:
            diagnostics.extend(_require_type(relpath, f"{field_name}.items", items, dict))
        if isinstance(items, dict):
            diagnostics.extend(_validate_body_schema(relpath, f"{field_name}.items", items))

    enum_values = schema_fragment.get("enum")
    if enum_values is not None:
        diagnostics.extend(_require_type(relpath, f"{field_name}.enum", enum_values, list))
        if isinstance(enum_values, list) and len(enum_values) == 0:
            diagnostics.append(
                ValidationDiagnostic(
                    code=SCHEMA_INVALID_VALUE,
                    severity="error",
                    message=f"Field '{field_name}.enum' must not be empty when provided.",
                    location=f"{relpath}:{field_name}.enum",
                    rule=RULE_FIELD_VALUE,
                )
            )

    if "example" in schema_fragment:
        diagnostics.extend(
            _validate_schema_example(
                relpath=relpath,
                field_name=field_name,
                schema_fragment=schema_fragment,
                example_value=schema_fragment.get("example"),
            )
        )

    if isinstance(declared_type, str):
        if declared_type != "object" and properties is not None:
            diagnostics.append(
                ValidationDiagnostic(
                    code=SCHEMA_INVALID_VALUE,
                    severity="error",
                    message=f"Field '{field_name}.properties' is only valid when type is object.",
                    location=f"{relpath}:{field_name}.properties",
                    rule=RULE_FIELD_VALUE,
                )
            )
        if declared_type != "array" and items is not None:
            diagnostics.append(
                ValidationDiagnostic(
                    code=SCHEMA_INVALID_VALUE,
                    severity="error",
                    message=f"Field '{field_name}.items' is only valid when type is array.",
                    location=f"{relpath}:{field_name}.items",
                    rule=RULE_FIELD_VALUE,
                )
            )

    return diagnostics


def _validate_schema_example(
    relpath: str, field_name: str, schema_fragment: dict[str, Any], example_value: Any
) -> list[ValidationDiagnostic]:
    diagnostics: list[ValidationDiagnostic] = []
    declared_type = schema_fragment.get("type")
    enum_values = schema_fragment.get("enum")
    properties = schema_fragment.get("properties")
    items = schema_fragment.get("items")

    if isinstance(enum_values, list) and example_value not in enum_values:
        diagnostics.append(
            ValidationDiagnostic(
                code=SCHEMA_INVALID_VALUE,
                severity="error",
                message=(
                    f"Field '{field_name}.example' must be one of the enum values declared in "
                    f"'{field_name}.enum'."
                ),
                location=f"{relpath}:{field_name}.example",
                rule=RULE_FIELD_VALUE,
            )
        )

    if not isinstance(declared_type, str):
        return diagnostics

    if not _is_example_type_compatible(declared_type, example_value):
        diagnostics.append(
            ValidationDiagnostic(
                code=SCHEMA_INVALID_VALUE,
                severity="error",
                message=(
                    f"Field '{field_name}.example' must be compatible with type '{declared_type}'."
                ),
                location=f"{relpath}:{field_name}.example",
                rule=RULE_FIELD_VALUE,
            )
        )
        return diagnostics

    if (
        declared_type == "object"
        and isinstance(properties, dict)
        and isinstance(example_value, dict)
    ):
        unknown_keys = sorted(key for key in example_value if key not in properties)
        for key in unknown_keys:
            diagnostics.append(
                ValidationDiagnostic(
                    code=SCHEMA_INVALID_VALUE,
                    severity="error",
                    message=(
                        f"Field '{field_name}.example.{key}' is not declared in "
                        f"'{field_name}.properties'."
                    ),
                    location=f"{relpath}:{field_name}.example.{key}",
                    rule=RULE_FIELD_VALUE,
                )
            )

        for prop_name, prop_schema in sorted(properties.items()):
            if not isinstance(prop_schema, dict):
                continue
            if prop_schema.get("required") is True and prop_name not in example_value:
                diagnostics.append(
                    ValidationDiagnostic(
                        code=SCHEMA_INVALID_VALUE,
                        severity="error",
                        message=(
                            f"Field '{field_name}.example' must include required property "
                            f"'{prop_name}'."
                        ),
                        location=f"{relpath}:{field_name}.example.{prop_name}",
                        rule=RULE_FIELD_VALUE,
                    )
                )

        for prop_name, prop_schema in sorted(properties.items()):
            if prop_name not in example_value or not isinstance(prop_schema, dict):
                continue
            diagnostics.extend(
                _validate_schema_example(
                    relpath=relpath,
                    field_name=f"{field_name}.properties.{prop_name}",
                    schema_fragment=prop_schema,
                    example_value=example_value[prop_name],
                )
            )

    if declared_type == "array" and isinstance(items, dict) and isinstance(example_value, list):
        for item in example_value:
            diagnostics.extend(
                _validate_schema_example(
                    relpath=relpath,
                    field_name=f"{field_name}.items",
                    schema_fragment=items,
                    example_value=item,
                )
            )

    return diagnostics


def _is_example_type_compatible(declared_type: str, example_value: Any) -> bool:
    if declared_type == "object":
        return isinstance(example_value, dict)
    if declared_type == "array":
        return isinstance(example_value, list)
    if declared_type == "string":
        return isinstance(example_value, str)
    if declared_type == "integer":
        return isinstance(example_value, int) and not isinstance(example_value, bool)
    if declared_type == "number":
        return (isinstance(example_value, int | float)) and not isinstance(example_value, bool)
    if declared_type == "boolean":
        return isinstance(example_value, bool)
    if declared_type == "null":
        return example_value is None
    return True


def _normalize_error_example(
    relpath: str,
    prefix: str,
    error_item: dict[str, Any],
    diagnostics: list[ValidationDiagnostic],
) -> dict[str, Any]:
    normalized_error = dict(error_item)
    if "example" not in normalized_error:
        return normalized_error

    short_example = normalized_error.pop("example")
    body = normalized_error.get("body")
    if not isinstance(body, dict):
        return normalized_error

    normalized_body = dict(body)
    if "example" in normalized_body:
        nested_example = normalized_body.get("example")
        if short_example != nested_example:
            diagnostics.append(
                ValidationDiagnostic(
                    code=SCHEMA_INVALID_VALUE,
                    severity="error",
                    message=(
                        f"Field '{prefix}.example' conflicts with " f"'{prefix}.body.example'."
                    ),
                    location=f"{relpath}:{prefix}.example",
                    rule=RULE_FIELD_VALUE,
                )
            )
    else:
        normalized_body["example"] = short_example
    normalized_error["body"] = normalized_body
    return normalized_error


def _validate_request_path_consistency(
    *,
    relpath: str,
    route_path: Any,
    request: Any,
    request_path_fragment: Any,
    skip_checks: bool,
) -> list[ValidationDiagnostic]:
    if skip_checks or not isinstance(route_path, str):
        return []

    placeholders = PATH_PLACEHOLDER_PATTERN.findall(route_path)
    if not placeholders:
        return []

    duplicate_placeholders = sorted({name for name in placeholders if placeholders.count(name) > 1})
    if duplicate_placeholders:
        duplicate_list = ", ".join(duplicate_placeholders)
        return [
            ValidationDiagnostic(
                code=DUPLICATE_PATH_PLACEHOLDER,
                severity="error",
                message=f"Duplicate path placeholder(s): {duplicate_list}.",
                location=f"{relpath}:path",
                rule=RULE_FIELD_VALUE,
            )
        ]

    if not isinstance(request, dict) or not isinstance(request_path_fragment, dict):
        return [
            ValidationDiagnostic(
                code=MISSING_REQUEST_PATH,
                severity="error",
                message=("Field 'request.path' is required when route path contains placeholders."),
                location=f"{relpath}:request.path",
                rule=RULE_REQUIRED_FIELD,
            )
        ]

    request_properties = request_path_fragment.get("properties")
    request_path_names = set(request_properties) if isinstance(request_properties, dict) else set()
    route_path_names = set(placeholders)
    if request_path_names == route_path_names:
        return []

    missing = sorted(route_path_names - request_path_names)
    extra = sorted(request_path_names - route_path_names)
    parts: list[str] = []
    if missing:
        parts.append(f"missing={','.join(missing)}")
    if extra:
        parts.append(f"extra={','.join(extra)}")
    details = "; ".join(parts)
    return [
        ValidationDiagnostic(
            code=REQUEST_PATH_MISMATCH,
            severity="error",
            message=f"Route path placeholders and request.path mismatch: {details}.",
            location=f"{relpath}:request.path",
            rule=RULE_FIELD_VALUE,
        )
    ]


def _report_unknown_fields(
    relpath: str,
    context_name: str,
    payload: dict[str, Any],
    allowed_fields: set[str],
    *,
    diagnostic_code: str = SCHEMA_UNKNOWN_FIELD,
) -> list[ValidationDiagnostic]:
    diagnostics: list[ValidationDiagnostic] = []
    for field_name in sorted(payload):
        if field_name in allowed_fields:
            continue
        diagnostics.append(
            ValidationDiagnostic(
                code=diagnostic_code,
                severity="error",
                message=f"Unknown field '{field_name}' in {context_name}.",
                location=f"{relpath}:{context_name}.{field_name}",
                rule=RULE_FIELD_UNKNOWN,
            )
        )
    return diagnostics


def _location(relpath: Path) -> str:
    return relpath.as_posix()


def _type_name(expected_type: type[Any]) -> str:
    if expected_type is dict:
        return "object"
    if expected_type is list:
        return "array"
    return expected_type.__name__


def _validate_shorthand_ref(
    relpath: str, field_name: str, value: str
) -> list[ValidationDiagnostic]:
    if value.startswith("$") and len(value.strip()) > 1:
        return []
    return [
        ValidationDiagnostic(
            code=SCHEMA_INVALID_VALUE,
            severity="error",
            message=f"Field '{field_name}' must use '$ModelRef' shorthand for string refs.",
            location=f"{relpath}:{field_name}",
            rule=RULE_FIELD_VALUE,
        )
    ]


def _validate_ref_schema_node(
    relpath: str, field_name: str, schema_fragment: dict[str, Any]
) -> list[ValidationDiagnostic]:
    diagnostics: list[ValidationDiagnostic] = []
    ref_payload = dict(schema_fragment)
    try:
        parsed = RefSchemaNodeModel.model_validate(ref_payload)
    except ValidationError:
        parsed = None
    if parsed is None:
        ref_value = schema_fragment.get("$ref")
        if ref_value is None:
            diagnostics.append(
                ValidationDiagnostic(
                    code=SCHEMA_MISSING_FIELD,
                    severity="error",
                    message=f"Missing required field '{field_name}.$ref'.",
                    location=f"{relpath}:{field_name}.$ref",
                    rule=RULE_REQUIRED_FIELD,
                )
            )
        else:
            diagnostics.extend(_require_type(relpath, f"{field_name}.$ref", ref_value, str))
    else:
        if not parsed.ref.strip():
            diagnostics.append(
                ValidationDiagnostic(
                    code=SCHEMA_INVALID_VALUE,
                    severity="error",
                    message=f"Field '{field_name}.$ref' must be non-empty.",
                    location=f"{relpath}:{field_name}.$ref",
                    rule=RULE_FIELD_VALUE,
                )
            )

    forbidden_inline_fields = ("type", "properties", "items", "enum", "example")
    for field in forbidden_inline_fields:
        if field in schema_fragment:
            diagnostics.append(
                ValidationDiagnostic(
                    code=SCHEMA_INVALID_VALUE,
                    severity="error",
                    message=f"Field '{field_name}.{field}' is not allowed for '$ref' nodes.",
                    location=f"{relpath}:{field_name}.{field}",
                    rule=RULE_FIELD_VALUE,
                )
            )
    return diagnostics


def _validate_shared_model_contract(
    document: ContractDocument, data: dict[str, Any]
) -> tuple[None, list[ValidationDiagnostic]]:
    diagnostics: list[ValidationDiagnostic] = []
    relpath = _location(document.contract_relpath)

    diagnostics.extend(
        _report_unknown_fields(relpath, "contract", data, SHARED_ROOT_ALLOWED_FIELDS)
    )
    required_fields = ("contract_type", "name", "description", "model")
    for field_name in required_fields:
        if field_name not in data:
            diagnostics.append(
                ValidationDiagnostic(
                    code=SCHEMA_MISSING_FIELD,
                    severity="error",
                    message=f"Missing required field '{field_name}'.",
                    location=f"{relpath}:{field_name}",
                    rule=RULE_REQUIRED_FIELD,
                )
            )

    diagnostics.extend(_require_type(relpath, "name", data.get("name"), str))
    diagnostics.extend(_require_type(relpath, "description", data.get("description"), str))
    diagnostics.extend(_require_type(relpath, "model", data.get("model"), dict))

    if isinstance(data.get("name"), str) and not str(data.get("name")).strip():
        diagnostics.append(
            ValidationDiagnostic(
                code=SCHEMA_INVALID_VALUE,
                severity="error",
                message="Field 'name' must be non-empty.",
                location=f"{relpath}:name",
                rule=RULE_FIELD_VALUE,
            )
        )
    if isinstance(data.get("description"), str) and not str(data.get("description")).strip():
        diagnostics.append(
            ValidationDiagnostic(
                code=SCHEMA_INVALID_VALUE,
                severity="error",
                message="Field 'description' must be non-empty.",
                location=f"{relpath}:description",
                rule=RULE_FIELD_VALUE,
            )
        )

    try:
        payload = SharedModelContractModel.model_validate(data)
    except ValidationError:
        payload = None
    if payload is not None:
        if payload.contract_type.strip().lower() != "shared_model":
            diagnostics.append(
                ValidationDiagnostic(
                    code=SCHEMA_INVALID_VALUE,
                    severity="error",
                    message="Field 'contract_type' must be 'shared_model'.",
                    location=f"{relpath}:contract_type",
                    rule=RULE_FIELD_VALUE,
                )
            )
    elif isinstance(data.get("contract_type"), str):
        if str(data.get("contract_type")).strip().lower() != "shared_model":
            diagnostics.append(
                ValidationDiagnostic(
                    code=SCHEMA_INVALID_VALUE,
                    severity="error",
                    message="Field 'contract_type' must be 'shared_model'.",
                    location=f"{relpath}:contract_type",
                    rule=RULE_FIELD_VALUE,
                )
            )

    model_fragment = data.get("model")
    if isinstance(model_fragment, dict):
        diagnostics.extend(_validate_body_schema(relpath, "model", model_fragment))

    if diagnostics:
        return None, diagnostics
    return None, []
