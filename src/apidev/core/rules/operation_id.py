from collections import Counter

from apidev.core.models.operation import Operation


def build_operation_id(contract_relpath: str) -> str:
    path = contract_relpath.replace("\\", "/")
    parts = path.split("/")
    if len(parts) < 2:
        stem = parts[-1].rsplit(".", maxsplit=1)[0]
        return stem

    domain = parts[-2]
    stem = parts[-1].rsplit(".", maxsplit=1)[0]
    return f"{domain}_{stem}"


def ensure_unique_operation_ids(operations: list[Operation]) -> list[str]:
    counter = Counter(op.operation_id for op in operations)
    return [
        f"Duplicate operation_id: {operation_id}"
        for operation_id, count in counter.items()
        if count > 1
    ]
