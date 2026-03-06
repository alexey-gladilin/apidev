from pathlib import Path

from apidev.application.services.validate_service import ValidateService
from apidev.infrastructure.config.toml_loader import TomlConfigLoader
from apidev.infrastructure.contracts.yaml_loader import YamlContractLoader
from apidev.infrastructure.filesystem.local_fs import LocalFileSystem


def _write_contract(root: Path, relpath: str, body: str) -> None:
    target = root / ".apidev" / "contracts" / relpath
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body.strip(), encoding="utf-8")


def _write_shared_model(root: Path, relpath: str, body: str) -> None:
    target = root / ".apidev" / "models" / relpath
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body.strip(), encoding="utf-8")


def _run_validate(project_dir: Path):
    service = ValidateService(
        loader=YamlContractLoader(),
        config_loader=TomlConfigLoader(fs=LocalFileSystem()),
    )
    return service.run(project_dir)


def _valid_operation_contract(response_body: str) -> str:
    return f"""
method: GET
path: /v1/items
auth: public
summary: S
description: D
response:
  status: 200
  body:
{response_body}
errors: []
"""


def test_validate_reports_contract_type_location_mismatch_for_shared_contract_in_operations_dir(
    tmp_path: Path,
) -> None:
    _write_contract(
        tmp_path,
        "billing/shared_like.yaml",
        """
contract_type: shared_model
name: SortDescriptor
description: sort model
model:
  type: object
  properties:
    field:
      type: string
""",
    )

    result = _run_validate(tmp_path)

    assert any(d.code == "SEMANTIC_CONTRACT_TYPE_LOCATION_MISMATCH" for d in result.diagnostics)


def test_validate_reports_contract_type_location_mismatch_for_operation_in_shared_dir(
    tmp_path: Path,
) -> None:
    _write_shared_model(
        tmp_path,
        "billing/list_items.yaml",
        """
contract_type: operation
method: GET
path: /v1/items
auth: public
description: list
response:
  status: 200
  body:
    type: object
errors: []
""",
    )

    result = _run_validate(tmp_path)

    assert any(d.code == "SEMANTIC_CONTRACT_TYPE_LOCATION_MISMATCH" for d in result.diagnostics)


def test_validate_reports_missing_ref(tmp_path: Path) -> None:
    _write_contract(
        tmp_path,
        "billing/list_items.yaml",
        _valid_operation_contract("""
    type: object
    properties:
      pageInfo:
        $ref: common.PageInfo
"""),
    )

    result = _run_validate(tmp_path)

    assert any(d.code == "SEMANTIC_MISSING_MODEL_REFERENCE" for d in result.diagnostics)


def test_validate_reports_ambiguous_short_ref(tmp_path: Path) -> None:
    _write_shared_model(
        tmp_path,
        "common/page_info.yaml",
        """
contract_type: shared_model
name: PageInfo
description: common page info
model:
  type: object
  properties:
    total:
      type: integer
""",
    )
    _write_shared_model(
        tmp_path,
        "billing/page_info.yaml",
        """
contract_type: shared_model
name: PageInfo
description: billing page info
model:
  type: object
  properties:
    page:
      type: integer
""",
    )
    _write_contract(
        tmp_path,
        "billing/list_items.yaml",
        _valid_operation_contract("""
    type: object
    properties:
      pageInfo: $PageInfo
"""),
    )

    result = _run_validate(tmp_path)

    assert any(d.code == "SEMANTIC_AMBIGUOUS_MODEL_REFERENCE" for d in result.diagnostics)


def test_validate_reports_scope_leak_for_foreign_local_model_ref(tmp_path: Path) -> None:
    _write_contract(
        tmp_path,
        "users/create_user.yaml",
        """
method: POST
path: /v1/users
auth: bearer
summary: create
description: create
local_models:
  Address:
    type: object
    properties:
      city:
        type: string
response:
  status: 201
  body:
    type: object
errors: []
""",
    )
    _write_contract(
        tmp_path,
        "billing/list_items.yaml",
        _valid_operation_contract("""
    type: object
    properties:
      address: $Address
"""),
    )

    result = _run_validate(tmp_path)

    assert any(d.code == "SEMANTIC_SCOPE_LEAK" for d in result.diagnostics)


def test_validate_reports_duplicate_shared_model_keys(tmp_path: Path) -> None:
    _write_shared_model(
        tmp_path,
        "common/a.yaml",
        """
contract_type: shared_model
name: PageInfo
description: first
model:
  type: object
  properties:
    id:
      type: integer
""",
    )
    _write_shared_model(
        tmp_path,
        "common/b.yaml",
        """
contract_type: shared_model
name: PageInfo
description: second
model:
  type: object
  properties:
    name:
      type: string
""",
    )

    result = _run_validate(tmp_path)

    assert any(d.code == "SEMANTIC_DUPLICATE_SHARED_MODEL_NAME" for d in result.diagnostics)


def test_validate_reports_reference_cycles(tmp_path: Path) -> None:
    _write_shared_model(
        tmp_path,
        "common/a.yaml",
        """
contract_type: shared_model
name: A
description: A model
model:
  type: object
  properties:
    b:
      $ref: common.B
""",
    )
    _write_shared_model(
        tmp_path,
        "common/b.yaml",
        """
contract_type: shared_model
name: B
description: B model
model:
  type: object
  properties:
    a:
      $ref: common.A
""",
    )

    result = _run_validate(tmp_path)

    cycle_diagnostics = [
        d for d in result.diagnostics if d.code == "validation.CONTRACT_REFERENCE_CYCLE"
    ]
    assert cycle_diagnostics
    assert cycle_diagnostics[0].location.startswith("common/")
    assert cycle_diagnostics[0].context is not None
    assert cycle_diagnostics[0].context["cycle_path"] == [
        "shared_model:common.A",
        "shared_model:common.B",
        "shared_model:common.A",
    ]


def test_validate_reports_self_reference_cycle(tmp_path: Path) -> None:
    _write_shared_model(
        tmp_path,
        "common/node.yaml",
        """
contract_type: shared_model
name: Node
description: recursive node
model:
  type: object
  properties:
    next:
      $ref: common.Node
""",
    )

    result = _run_validate(tmp_path)

    cycle_diagnostics = [
        d for d in result.diagnostics if d.code == "validation.CONTRACT_REFERENCE_CYCLE"
    ]
    assert cycle_diagnostics
    assert cycle_diagnostics[0].context is not None
    assert cycle_diagnostics[0].context["cycle_path"] == [
        "shared_model:common.Node",
        "shared_model:common.Node",
    ]


def test_validate_reports_location_mismatch_for_implicit_operation_in_shared_dir(
    tmp_path: Path,
) -> None:
    _write_shared_model(
        tmp_path,
        "billing/search_items.yaml",
        """
method: GET
path: /v1/billing/search
auth: public
summary: search items
description: search items
response:
  status: 200
  body:
    type: object
errors: []
""",
    )

    result = _run_validate(tmp_path)

    assert any(d.code == "SEMANTIC_CONTRACT_TYPE_LOCATION_MISMATCH" for d in result.diagnostics)


def test_validate_accepts_nested_shared_refs_in_properties_and_items(tmp_path: Path) -> None:
    _write_shared_model(
        tmp_path,
        "common/page_info.yaml",
        """
contract_type: shared_model
name: PageInfo
description: paging metadata
model:
  type: object
  properties:
    total:
      type: integer
""",
    )
    _write_shared_model(
        tmp_path,
        "common/user_summary.yaml",
        """
contract_type: shared_model
name: UserSummary
description: user projection
model:
  type: object
  properties:
    id:
      type: string
""",
    )
    _write_contract(
        tmp_path,
        "users/list_users.yaml",
        """
method: POST
path: /v1/users/list
auth: public
summary: list users
description: list users
request:
  body:
    type: object
    properties:
      paging:
        $ref: common.PageInfo
response:
  status: 200
  body:
    type: object
    properties:
      pageInfo: $PageInfo
      items:
        type: array
        items: $common.UserSummary
errors: []
""",
    )

    result = _run_validate(tmp_path)
    blocking_codes = {
        "SEMANTIC_MISSING_MODEL_REFERENCE",
        "SEMANTIC_AMBIGUOUS_MODEL_REFERENCE",
        "SEMANTIC_SCOPE_LEAK",
        "validation.CONTRACT_REFERENCE_CYCLE",
    }
    assert all(d.code not in blocking_codes for d in result.diagnostics)


def test_validate_accepts_short_shared_ref_when_name_is_unique(tmp_path: Path) -> None:
    _write_shared_model(
        tmp_path,
        "catalog/filter.yaml",
        """
contract_type: shared_model
name: SearchFilter
description: shared search filter
model:
  type: object
  properties:
    query:
      type: string
""",
    )
    _write_contract(
        tmp_path,
        "catalog/search_items.yaml",
        """
method: GET
path: /v1/catalog/search
auth: public
summary: search items
description: search items
request:
  query:
    type: object
    properties:
      filter: $SearchFilter
response:
  status: 200
  body:
    type: object
errors: []
""",
    )

    result = _run_validate(tmp_path)
    blocking_codes = {
        "SEMANTIC_MISSING_MODEL_REFERENCE",
        "SEMANTIC_AMBIGUOUS_MODEL_REFERENCE",
        "SEMANTIC_SCOPE_LEAK",
    }
    assert all(d.code not in blocking_codes for d in result.diagnostics)
