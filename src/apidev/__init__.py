from importlib.metadata import PackageNotFoundError, version as package_version
from pathlib import Path
import tomllib

__all__ = ["__version__"]


def _resolve_package_version() -> str:
    pyproject_path = Path(__file__).resolve().parents[2] / "pyproject.toml"
    if pyproject_path.exists():
        try:
            payload = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
            project = payload.get("project")
            if isinstance(project, dict):
                pyproject_version = project.get("version")
                if isinstance(pyproject_version, str) and pyproject_version.strip():
                    return pyproject_version.strip()
        except Exception:
            pass

    try:
        return package_version("apidev")
    except PackageNotFoundError:
        return "0.0.0"


__version__ = _resolve_package_version()
