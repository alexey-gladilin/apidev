from pathlib import Path

from apidev.application.services.validate_service import ValidateService
from apidev.infrastructure.config.toml_loader import TomlConfigLoader
from apidev.infrastructure.contracts.yaml_loader import YamlContractLoader
from apidev.infrastructure.filesystem.local_fs import LocalFileSystem


def _write_contract(root: Path, relpath: str, body: str) -> None:
    target = root / ".apidev" / "contracts" / relpath
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body.strip(), encoding="utf-8")


def _run_validate(project_dir: Path):
    service = ValidateService(
        loader=YamlContractLoader(),
        config_loader=TomlConfigLoader(fs=LocalFileSystem()),
    )
    return service.run(project_dir)


def test_validate_reports_no_errors_for_minimal_contract(tmp_path: Path) -> None:
    _write_contract(
        tmp_path,
        "billing/create_invoice.yaml",
        """
method: POST
path: /v1/invoices
auth: bearer
summary: Create invoice
description: Create invoice
intent: write
access_pattern: imperative
response:
  status: 201
  body: {type: object}
errors: []
""",
    )

    result = _run_validate(tmp_path)

    assert not result.diagnostics
    assert len(result.operations) == 1


def test_validate_inline_only_contract_does_not_require_shared_models_dir(tmp_path: Path) -> None:
    _write_contract(
        tmp_path,
        "users/list_users.yaml",
        """
method: GET
path: /v1/users
auth: bearer
summary: List users
description: Legacy inline-only contract.
intent: read
access_pattern: cached
response:
  status: 200
  body:
    type: object
    properties:
      items:
        type: array
        items:
          type: object
          properties:
            id:
              type: integer
              required: true
            name:
              type: string
              required: true
errors: []
""",
    )

    result = _run_validate(tmp_path)

    assert not result.has_errors
    assert len(result.operations) == 1


def test_validate_inline_only_contract_with_custom_shared_models_dir_stays_compatible(
    tmp_path: Path,
) -> None:
    (tmp_path / ".apidev").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".apidev" / "config.toml").write_text(
        """[inputs]
contracts_dir = ".apidev/contracts"
shared_models_dir = ".apidev/shared-models"
""".strip(),
        encoding="utf-8",
    )
    _write_contract(
        tmp_path,
        "billing/get_invoice.yaml",
        """
method: GET
path: /v1/invoices/{invoice_id}
auth: bearer
summary: Get invoice
description: Inline-only legacy contract with custom config.
intent: read
access_pattern: cached
request:
  path:
    type: object
    properties:
      invoice_id:
        type: integer
        required: true
response:
  status: 200
  body:
    type: object
    properties:
      invoice_id:
        type: integer
        required: true
errors: []
""",
    )

    result = _run_validate(tmp_path)

    assert not result.has_errors
    assert len(result.operations) == 1


def test_validate_reports_schema_errors_for_missing_fields(tmp_path: Path) -> None:
    _write_contract(
        tmp_path,
        "billing/bad_contract.yaml",
        """
path: v1/invoices
auth: bearer
summary: Create invoice
description: Create invoice
response:
  status: "201"
  body: []
errors: {}
""",
    )

    result = _run_validate(tmp_path)

    assert result.has_errors
    assert len(result.operations) == 0
    assert {diagnostic.code for diagnostic in result.diagnostics} >= {
        "SCHEMA_MISSING_FIELD",
        "SCHEMA_INVALID_TYPE",
        "SCHEMA_INVALID_VALUE",
    }
    assert all(diagnostic.rule.startswith("schema.") for diagnostic in result.diagnostics)


def test_validate_reports_duplicate_operation_id_with_locations(tmp_path: Path) -> None:
    valid_contract = """
method: GET
path: /v1/items
auth: bearer
summary: Get item
description: Get item
intent: read
access_pattern: cached
response:
  status: 200
  body: {type: object}
errors: []
"""
    _write_contract(tmp_path, "domain_a/orders/get_item.yaml", valid_contract)
    _write_contract(tmp_path, "domain_b/orders/get_item.yaml", valid_contract)

    result = _run_validate(tmp_path)

    duplicate = [
        diagnostic
        for diagnostic in result.diagnostics
        if diagnostic.code == "SEMANTIC_DUPLICATE_OPERATION_ID"
    ]
    assert len(duplicate) == 1
    assert duplicate[0].rule == "semantic.operation_id.unique"
    assert duplicate[0].location == "domain_a/orders/get_item.yaml,domain_b/orders/get_item.yaml"


def test_validate_reports_invalid_operation_id_format_from_filename(tmp_path: Path) -> None:
    _write_contract(
        tmp_path,
        "billing/bad-name.yaml",
        """
method: GET
path: /v1/items
auth: bearer
summary: Get item
description: Get item
intent: read
access_pattern: cached
response:
  status: 200
  body: {type: object}
errors: []
""",
    )

    result = _run_validate(tmp_path)

    invalid = [
        diagnostic
        for diagnostic in result.diagnostics
        if diagnostic.code == "SEMANTIC_INVALID_OPERATION_ID"
    ]
    assert len(invalid) == 1
    assert invalid[0].rule == "semantic.operation_id.format"
    assert invalid[0].location == "billing/bad-name.yaml"


def test_validate_diagnostics_order_is_deterministic(tmp_path: Path) -> None:
    _write_contract(
        tmp_path,
        "b/contract.yaml",
        """
path: missing-leading-slash
auth: bearer
summary: Contract
description: Contract
response:
  body: {}
errors: []
""",
    )
    _write_contract(
        tmp_path,
        "a/contract.yaml",
        """
path: /ok
auth: bearer
summary: Contract
description: Contract
response:
  status: "200"
  body: {}
errors: []
""",
    )

    result = _run_validate(tmp_path)

    ordered_locations = [diagnostic.location for diagnostic in result.diagnostics]
    assert ordered_locations == sorted(ordered_locations)


def test_validate_reports_semantic_invalid_operation_metadata_values(tmp_path: Path) -> None:
    _write_contract(
        tmp_path,
        "users/search.yaml",
        """
method: POST
path: /v1/users/search
auth: bearer
summary: Search users
description: Search users by filters.
intent: mutate
access_pattern: streaming
response:
  status: 200
  body: {type: object}
errors: []
""",
    )

    result = _run_validate(tmp_path)

    metadata_diagnostics = [
        diagnostic
        for diagnostic in result.diagnostics
        if diagnostic.location in {"users/search.yaml:intent", "users/search.yaml:access_pattern"}
    ]
    assert [diagnostic.rule for diagnostic in metadata_diagnostics] == [
        "semantic.operation_metadata.allowed_value",
        "semantic.operation_metadata.allowed_value",
    ]
    assert [diagnostic.location for diagnostic in metadata_diagnostics] == [
        "users/search.yaml:access_pattern",
        "users/search.yaml:intent",
    ]


def test_validate_reports_semantic_invalid_operation_metadata_combination(tmp_path: Path) -> None:
    _write_contract(
        tmp_path,
        "users/search.yaml",
        """
method: POST
path: /v1/users/search
auth: bearer
summary: Search users
description: Search users by filters.
intent: write
access_pattern: cached
response:
  status: 200
  body: {type: object}
errors: []
""",
    )

    result = _run_validate(tmp_path)

    metadata_diagnostics = [
        diagnostic
        for diagnostic in result.diagnostics
        if diagnostic.location.startswith("users/search.yaml:")
    ]
    assert [diagnostic.rule for diagnostic in metadata_diagnostics] == [
        "semantic.operation_metadata.compatibility"
    ]
    assert [diagnostic.location for diagnostic in metadata_diagnostics] == [
        "users/search.yaml:access_pattern"
    ]


def test_validate_reports_nested_schema_type_errors(tmp_path: Path) -> None:
    _write_contract(
        tmp_path,
        "system/health.yaml",
        """
method: GET
path: /v1/health
auth: public
summary: Health endpoint
description: Returns health status.
response:
  status: 200
  body:
    type: object11
    properties:
      status:
        type: string11
        required: true
errors:
  - code: INTERNAL_ERROR
    http_status: 500
    body:
      type: object
      properties:
        error_code:
          type: string
          required: true
""",
    )

    result = _run_validate(tmp_path)

    assert result.has_errors
    assert any(d.location.endswith("response.body.type") for d in result.diagnostics)
    assert any(
        d.location.endswith("response.body.properties.status.type") for d in result.diagnostics
    )


def test_validate_rejects_invalid_http_method_and_auth(tmp_path: Path) -> None:
    _write_contract(
        tmp_path,
        "system/health.yaml",
        """
method: GETоооо
path: /v1/health
auth: token
summary: Health endpoint
description: Returns health status.
response:
  status: 200
  body:
    type: object
    properties:
      status:
        type: string
        required: true
errors: []
""",
    )

    result = _run_validate(tmp_path)

    locations = {d.location for d in result.diagnostics}
    assert result.has_errors
    assert "system/health.yaml:method" in locations
    assert "system/health.yaml:auth" in locations


def test_validate_rejects_unknown_fields_and_invalid_status_ranges(tmp_path: Path) -> None:
    _write_contract(
        tmp_path,
        "billing/bad.yaml",
        """
method: GET
path: /v1/items
auth: public
summary: S
description: D
x_unknown: true
response:
  status: 700
  body:
    type: object
    properties: {}
  x_extra: true
errors:
  - code: INTERNAL_ERROR
    http_status: 200
    body:
      type: object
      properties: {}
    x_more: true
""",
    )

    result = _run_validate(tmp_path)

    codes = {d.code for d in result.diagnostics}
    assert "SCHEMA_UNKNOWN_FIELD" in codes
    assert "SCHEMA_INVALID_VALUE" in codes
    assert any("contract.x_unknown" in d.location for d in result.diagnostics)
    assert any("response.x_extra" in d.location for d in result.diagnostics)
    assert any("errors[0].x_more" in d.location for d in result.diagnostics)
    assert any(d.location.endswith("response.status") for d in result.diagnostics)
    assert any(d.location.endswith("errors[0].http_status") for d in result.diagnostics)


def test_validate_rejects_unsafe_path_characters_for_codegen(tmp_path: Path) -> None:
    _write_contract(
        tmp_path,
        "billing/unsafe_path.yaml",
        """
method: GET
path: '/x"+__import__("os").system("echo_INJECTED")+"'
auth: public
summary: Unsafe
description: Unsafe
response:
  status: 200
  body:
    type: object
    properties: {}
errors: []
""",
    )

    result = _run_validate(tmp_path)

    assert result.has_errors
    assert any(
        d.location.endswith(":path") and d.code == "SCHEMA_INVALID_VALUE"
        for d in result.diagnostics
    )


def test_validate_rejects_invalid_error_code_format_and_duplicates(tmp_path: Path) -> None:
    _write_contract(
        tmp_path,
        "billing/errors.yaml",
        """
method: GET
path: /v1/items
auth: public
summary: S
description: D
intent: read
access_pattern: cached
response:
  status: 200
  body:
    type: object
    properties: {}
errors:
  - code: internal_error
    http_status: 500
    body:
      type: object
      properties: {}
  - code: internal_error
    http_status: 501
    body:
      type: object
      properties: {}
""",
    )

    result = _run_validate(tmp_path)

    assert result.has_errors
    assert any(
        d.message == "Field 'errors[0].code' must use UPPER_SNAKE_CASE format."
        for d in result.diagnostics
    )
    assert any("Duplicate error code" in d.message for d in result.diagnostics)


def test_validate_rejects_inconsistent_object_and_array_schema_shapes(tmp_path: Path) -> None:
    _write_contract(
        tmp_path,
        "billing/shape.yaml",
        """
method: GET
path: /v1/items
auth: public
summary: S
description: D
intent: read
access_pattern: cached
response:
  status: 200
  body:
    type: string
    properties: {}
errors:
  - code: INTERNAL_ERROR
    http_status: 500
    body:
      type: object
      items:
        type: string
""",
    )

    result = _run_validate(tmp_path)

    assert result.has_errors
    assert any(d.location.endswith("response.body.properties") for d in result.diagnostics)
    assert any(d.location.endswith("errors[0].body.items") for d in result.diagnostics)


def test_validate_rejects_empty_enum_and_invalid_required_flag(tmp_path: Path) -> None:
    _write_contract(
        tmp_path,
        "billing/enum.yaml",
        """
method: GET
path: /v1/items
auth: public
summary: S
description: D
intent: read
access_pattern: cached
response:
  status: 200
  body:
    type: object
    properties:
      status:
        type: string
        enum: []
        required: "true"
errors: []
""",
    )

    result = _run_validate(tmp_path)

    assert result.has_errors
    assert any(
        d.location.endswith("response.body.properties.status.enum") for d in result.diagnostics
    )
    assert any(
        d.location.endswith("response.body.properties.status.required")
        and d.code == "SCHEMA_INVALID_TYPE"
        for d in result.diagnostics
    )


def test_validate_reports_invalid_yaml_parse_error(tmp_path: Path) -> None:
    _write_contract(
        tmp_path,
        "billing/invalid_yaml.yaml",
        """
method: GET
path: /v1/items
auth: public
summary: S
description: D
intent: read
access_pattern: cached
response:
  status: 200
  body:
    type: object
    properties:
      a:
        type: string
      b
errors: []
""",
    )

    result = _run_validate(tmp_path)

    assert result.has_errors
    assert any(d.code == "SCHEMA_INVALID_YAML" for d in result.diagnostics)


def test_validate_reports_duplicate_method_path_signature(tmp_path: Path) -> None:
    base_contract = """
method: GET
path: /v1/items
auth: public
summary: S
description: D
intent: read
access_pattern: cached
response:
  status: 200
  body:
    type: object
    properties: {}
errors: []
"""
    _write_contract(tmp_path, "catalog/list_items.yaml", base_contract)
    _write_contract(tmp_path, "inventory/fetch_items.yaml", base_contract)

    result = _run_validate(tmp_path)

    duplicates = [
        d for d in result.diagnostics if d.code == "SEMANTIC_DUPLICATE_ENDPOINT_SIGNATURE"
    ]
    assert len(duplicates) == 1
    assert duplicates[0].rule == "semantic.endpoint_signature.unique"


def test_validate_accepts_schema_level_example_in_schema_fragments(tmp_path: Path) -> None:
    _write_contract(
        tmp_path,
        "billing/with_examples.yaml",
        """
method: GET
path: /v1/items
auth: public
summary: S
description: D
intent: read
access_pattern: cached
response:
  status: 200
  body:
    type: object
    example:
      id: 1
      tags:
        - sale
    properties:
      id:
        type: integer
        example: 1
      tags:
        type: array
        example:
          - sale
        items:
          type: string
          example: sale
errors:
  - code: INTERNAL_ERROR
    http_status: 500
    body:
      type: object
      example:
        message: internal
      properties:
        message:
          type: string
          example: internal
""",
    )

    result = _run_validate(tmp_path)

    assert not result.has_errors
    assert len(result.operations) == 1


def test_validate_rejects_root_level_examples_as_unknown_field(tmp_path: Path) -> None:
    _write_contract(
        tmp_path,
        "billing/root_examples.yaml",
        """
method: GET
path: /v1/items
auth: public
summary: S
description: D
examples: []
response:
  status: 200
  body:
    type: object
errors: []
""",
    )

    result = _run_validate(tmp_path)

    assert result.has_errors
    assert any(
        d.code == "SCHEMA_UNKNOWN_FIELD" and d.location.endswith("contract.examples")
        for d in result.diagnostics
    )


def test_validate_rejects_schema_example_type_and_enum_mismatch(tmp_path: Path) -> None:
    _write_contract(
        tmp_path,
        "billing/bad_example_type_enum.yaml",
        """
method: GET
path: /v1/items
auth: public
summary: S
description: D
intent: read
access_pattern: cached
response:
  status: 200
  body:
    type: object
    properties:
      count:
        type: integer
        example: "42"
      status:
        type: string
        enum: [NEW, DONE]
        example: ARCHIVED
errors: []
""",
    )

    result = _run_validate(tmp_path)

    assert result.has_errors
    assert any(
        d.location.endswith("response.body.properties.count.example")
        and d.code == "SCHEMA_INVALID_VALUE"
        for d in result.diagnostics
    )
    assert any(
        d.location.endswith("response.body.properties.status.example")
        and d.code == "SCHEMA_INVALID_VALUE"
        for d in result.diagnostics
    )
    assert not any(
        d.code == "SCHEMA_UNKNOWN_FIELD" and ".example" in d.location for d in result.diagnostics
    )


def test_validate_rejects_schema_example_container_shape_mismatch(tmp_path: Path) -> None:
    _write_contract(
        tmp_path,
        "billing/bad_example_shape.yaml",
        """
method: GET
path: /v1/items
auth: public
summary: S
description: D
intent: read
access_pattern: cached
response:
  status: 200
  body:
    type: object
    example: "not-object"
    properties:
      tags:
        type: array
        example: "not-array"
        items:
          type: string
errors: []
""",
    )

    result = _run_validate(tmp_path)

    assert result.has_errors
    assert any(
        d.location.endswith("response.body.example") and d.code == "SCHEMA_INVALID_VALUE"
        for d in result.diagnostics
    )
    assert any(
        d.location.endswith("response.body.properties.tags.example")
        and d.code == "SCHEMA_INVALID_VALUE"
        for d in result.diagnostics
    )


def test_validate_accepts_null_example_for_null_type(tmp_path: Path) -> None:
    _write_contract(
        tmp_path,
        "billing/null_example.yaml",
        """
method: GET
path: /v1/items
auth: public
summary: S
description: D
intent: read
access_pattern: cached
response:
  status: 200
  body:
    type: object
    properties:
      archived_at:
        type: "null"
        example: null
errors: []
""",
    )

    result = _run_validate(tmp_path)

    assert not result.has_errors


def test_validate_rejects_schema_example_unknown_and_missing_required_properties(
    tmp_path: Path,
) -> None:
    _write_contract(
        tmp_path,
        "billing/bad_example_object_keys.yaml",
        """
method: GET
path: /v1/items
auth: public
summary: S
description: D
response:
  status: 200
  body:
    type: object
    example:
      id: item-1
      extra: unexpected
    properties:
      id:
        type: string
        required: true
      status:
        type: string
        required: true
errors: []
""",
    )

    result = _run_validate(tmp_path)

    assert result.has_errors
    assert any(
        d.location.endswith("response.body.example.extra") and d.code == "SCHEMA_INVALID_VALUE"
        for d in result.diagnostics
    )
    assert any(
        d.location.endswith("response.body.example.status") and d.code == "SCHEMA_INVALID_VALUE"
        for d in result.diagnostics
    )


def test_validate_rejects_nested_array_item_example_unknown_and_missing_required(
    tmp_path: Path,
) -> None:
    _write_contract(
        tmp_path,
        "billing/bad_nested_item_example.yaml",
        """
method: GET
path: /v1/items
auth: public
summary: S
description: D
response:
  status: 200
  body:
    type: object
    properties:
      items:
        type: array
        items:
          type: object
          properties:
            id:
              type: string
              required: true
            status:
              type: string
              required: true
        example:
          - id: item-1
            extra: unexpected
errors: []
""",
    )

    result = _run_validate(tmp_path)

    assert result.has_errors
    assert any(
        d.location.endswith("response.body.properties.items.items.example.extra")
        and d.code == "SCHEMA_INVALID_VALUE"
        for d in result.diagnostics
    )
    assert any(
        d.location.endswith("response.body.properties.items.items.example.status")
        and d.code == "SCHEMA_INVALID_VALUE"
        for d in result.diagnostics
    )


def test_validate_accepts_short_form_error_example(tmp_path: Path) -> None:
    _write_contract(
        tmp_path,
        "billing/short_form_error_example.yaml",
        """
method: GET
path: /v1/items/{item_id}
auth: public
summary: S
description: D
intent: read
access_pattern: cached
request:
  path:
    type: object
    properties:
      item_id:
        type: string
        required: true
response:
  status: 200
  body:
    type: object
errors:
  - code: ITEM_NOT_FOUND
    http_status: 404
    example:
      code: ITEM_NOT_FOUND
    body:
      type: object
      properties:
        code:
          type: string
          required: true
""",
    )

    result = _run_validate(tmp_path)

    assert not result.has_errors
    assert len(result.operations) == 1


def test_validate_accepts_equivalent_short_and_nested_error_examples(tmp_path: Path) -> None:
    _write_contract(
        tmp_path,
        "billing/equivalent_error_examples.yaml",
        """
method: GET
path: /v1/items/{item_id}
auth: public
summary: S
description: D
intent: read
access_pattern: cached
request:
  path:
    type: object
    properties:
      item_id:
        type: string
        required: true
response:
  status: 200
  body:
    type: object
errors:
  - code: ITEM_NOT_FOUND
    http_status: 404
    example:
      code: ITEM_NOT_FOUND
    body:
      type: object
      example:
        code: ITEM_NOT_FOUND
      properties:
        code:
          type: string
          required: true
""",
    )

    result = _run_validate(tmp_path)

    assert not result.has_errors
    assert len(result.operations) == 1


def test_validate_rejects_conflicting_short_and_nested_error_examples(tmp_path: Path) -> None:
    _write_contract(
        tmp_path,
        "billing/conflicting_error_examples.yaml",
        """
method: GET
path: /v1/items/{item_id}
auth: public
summary: S
description: D
response:
  status: 200
  body:
    type: object
errors:
  - code: ITEM_NOT_FOUND
    http_status: 404
    example:
      code: ITEM_NOT_FOUND
    body:
      type: object
      example:
        code: OTHER_ERROR
      properties:
        code:
          type: string
          required: true
""",
    )

    result = _run_validate(tmp_path)

    assert result.has_errors
    assert any(
        d.location.endswith("errors[0].example")
        and d.code == "SCHEMA_INVALID_VALUE"
        and "conflicts with 'errors[0].body.example'" in d.message
        for d in result.diagnostics
    )
