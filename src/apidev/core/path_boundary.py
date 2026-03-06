from pathlib import Path


def is_path_within_root(candidate: Path, root: Path) -> bool:
    try:
        candidate.relative_to(root)
        return True
    except ValueError:
        return False


def is_resolved_path_within_root(candidate: Path, root: Path) -> bool:
    resolved_root = root.resolve(strict=False)
    resolved_candidate = candidate.resolve(strict=False)
    return is_path_within_root(resolved_candidate, resolved_root)


def resolve_relative_path_within_root(root: Path, raw_path: str | Path) -> Path | None:
    candidate = Path(raw_path)
    if candidate.is_absolute():
        return None

    resolved_root = root.resolve(strict=False)
    resolved_candidate = (resolved_root / candidate).resolve(strict=False)
    if not is_path_within_root(resolved_candidate, resolved_root):
        return None
    return resolved_candidate
