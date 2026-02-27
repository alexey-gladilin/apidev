from collections import defaultdict

from apidev.core.models.diagnostic import ValidationDiagnostic
from apidev.core.models.operation import Operation

SEMANTIC_DUPLICATE_OPERATION_ID = "SEMANTIC_DUPLICATE_OPERATION_ID"
SEMANTIC_DUPLICATE_ENDPOINT_SIGNATURE = "SEMANTIC_DUPLICATE_ENDPOINT_SIGNATURE"
RULE_OPERATION_ID_UNIQUE = "semantic.operation_id.unique"
RULE_ENDPOINT_SIGNATURE_UNIQUE = "semantic.endpoint_signature.unique"


def validate_semantic_rules(operations: list[Operation]) -> list[ValidationDiagnostic]:
    by_operation_id: dict[str, list[Operation]] = defaultdict(list)
    by_endpoint_signature: dict[tuple[str, str], list[Operation]] = defaultdict(list)
    for operation in operations:
        by_operation_id[operation.operation_id].append(operation)
        key = (operation.contract.method, operation.contract.path)
        by_endpoint_signature[key].append(operation)

    diagnostics: list[ValidationDiagnostic] = []
    for operation_id in sorted(by_operation_id):
        bucket = by_operation_id[operation_id]
        if len(bucket) < 2:
            continue

        locations = sorted(operation.contract_relpath.as_posix() for operation in bucket)
        diagnostics.append(
            ValidationDiagnostic(
                code=SEMANTIC_DUPLICATE_OPERATION_ID,
                severity="error",
                message=f"Duplicate operation_id '{operation_id}'.",
                location=",".join(locations),
                rule=RULE_OPERATION_ID_UNIQUE,
            )
        )

    for method_path in sorted(by_endpoint_signature):
        bucket = by_endpoint_signature[method_path]
        if len(bucket) < 2:
            continue

        method, path = method_path
        locations = sorted(operation.contract_relpath.as_posix() for operation in bucket)
        diagnostics.append(
            ValidationDiagnostic(
                code=SEMANTIC_DUPLICATE_ENDPOINT_SIGNATURE,
                severity="error",
                message=f"Duplicate endpoint signature '{method} {path}'.",
                location=",".join(locations),
                rule=RULE_ENDPOINT_SIGNATURE_UNIQUE,
            )
        )

    return diagnostics
