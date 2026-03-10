from pathlib import Path

from apidev.infrastructure.contracts.yaml_loader import YamlContractLoader


def test_yaml_loader_skips_shared_model_contracts_when_loading_operations(tmp_path: Path) -> None:
    contracts_root = tmp_path / ".apidev" / "contracts"
    contracts_root.mkdir(parents=True, exist_ok=True)

    (contracts_root / "users").mkdir(parents=True, exist_ok=True)
    (contracts_root / "users" / "get_user.yaml").write_text(
        """
method: GET
path: /v1/users/{user_id}
auth: bearer
description: Get user.
intent: read
access_pattern: cached
request:
  path:
    type: object
    properties:
      user_id:
        type: string
response:
  status: 200
  body:
    $ref: users.User
errors: []
""".strip(),
        encoding="utf-8",
    )

    (contracts_root / "users" / "shared_user.yaml").write_text(
        """
contract_type: shared_model
name: User
description: User model.
model:
  type: object
  properties:
    id:
      type: string
      required: true
""".strip(),
        encoding="utf-8",
    )

    operations = YamlContractLoader().load(contracts_root)

    assert len(operations) == 1
    assert operations[0].operation_id == "users_get_user"
