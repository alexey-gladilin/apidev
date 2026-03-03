"""Generate Homebrew formula from release artifacts."""

from __future__ import annotations

import argparse
import hashlib
import os
import platform
import subprocess
from dataclasses import dataclass
from pathlib import Path

import tomllib


ROOT_DIR = Path(__file__).resolve().parents[2]
DIST_RELEASE_DIR = ROOT_DIR / "dist" / "release"
PYPROJECT_PATH = ROOT_DIR / "pyproject.toml"


@dataclass(frozen=True)
class MacosArtifact:
    arch: str
    binary_name: str
    checksum: str


def _normalize_version(value: str) -> str:
    version = value.strip()
    if version.startswith("v"):
        version = version[1:]
    return version


def _read_version_from_env() -> str | None:
    ref_name = os.getenv("GITHUB_REF_NAME", "").strip()
    if not ref_name:
        return None
    return _normalize_version(ref_name)


def _read_version_from_git_tag() -> str | None:
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--exact-match"],
            check=True,
            text=True,
            capture_output=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    tag = result.stdout.strip()
    if not tag:
        return None
    return _normalize_version(tag)


def read_version() -> str:
    env_version = _read_version_from_env()
    if env_version:
        return env_version

    git_tag_version = _read_version_from_git_tag()
    if git_tag_version:
        return git_tag_version

    data = tomllib.loads(PYPROJECT_PATH.read_text(encoding="utf-8"))
    return data["project"]["version"]


def normalize_arch(value: str) -> str:
    mapping = {
        "x64": "x86_64",
        "x86_64": "x86_64",
        "amd64": "x86_64",
        "arm64": "arm64",
        "aarch64": "arm64",
    }
    key = value.strip().lower()
    if key not in mapping:
        raise ValueError(f"Unsupported arch value: {value}")
    return mapping[key]


def detect_arch() -> str:
    return normalize_arch(platform.machine())


def sha256sum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _parse_macos_artifact_name(version: str, binary_name: str) -> str | None:
    prefix = f"apidev-{version}-macos-"
    if not binary_name.startswith(prefix):
        return None
    if not binary_name.endswith(".tar.gz"):
        return None
    arch = binary_name.removeprefix(prefix).removesuffix(".tar.gz")
    return normalize_arch(arch)


def collect_macos_artifacts(version: str, release_dir: Path) -> dict[str, MacosArtifact]:
    result: dict[str, MacosArtifact] = {}
    for artifact_path in sorted(release_dir.glob(f"apidev-{version}-macos-*.tar.gz")):
        arch = _parse_macos_artifact_name(version, artifact_path.name)
        if arch is None:
            continue
        result[arch] = MacosArtifact(
            arch=arch,
            binary_name=artifact_path.name,
            checksum=sha256sum(artifact_path),
        )
    if not result:
        raise ValueError(f"No macOS artifacts found in {release_dir}")
    return result


def render_formula(
    *,
    version: str,
    formula_class_name: str,
    repo_owner: str,
    repo_name: str,
    formula_name: str,
    asset_base_url: str,
    artifacts_by_arch: dict[str, MacosArtifact],
    default_arch: str,
) -> str:
    homepage = f"https://github.com/{repo_owner}/{repo_name}"
    base_url = asset_base_url.rstrip("/")

    lines = [
        f"class {formula_class_name} < Formula",
        '  desc "Contract-driven API code generator CLI"',
        f'  homepage "{homepage}"',
        f'  version "{version}"',
    ]

    arm_artifact = artifacts_by_arch.get("arm64")
    intel_artifact = artifacts_by_arch.get("x86_64")

    if arm_artifact and intel_artifact:
        lines.extend(
            [
                "  if Hardware::CPU.arm?",
                f'    url "{base_url}/{arm_artifact.binary_name}"',
                f'    sha256 "{arm_artifact.checksum}"',
                "  else",
                f'    url "{base_url}/{intel_artifact.binary_name}"',
                f'    sha256 "{intel_artifact.checksum}"',
                "  end",
            ]
        )
    else:
        artifact = artifacts_by_arch.get(default_arch) or next(iter(artifacts_by_arch.values()))
        lines.extend(
            [
                f'  url "{base_url}/{artifact.binary_name}"',
                f'  sha256 "{artifact.checksum}"',
            ]
        )

    lines.extend(
        [
            "",
            "  def install",
            f'    bin.install "{formula_name}"',
            "  end",
            "",
            "  test do",
            f'    assert_match "{formula_name}", shell_output("#{{bin}}/{formula_name} --help")',
            "  end",
            "end",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Homebrew formula from release artifacts")
    parser.add_argument("--version", default=read_version(), help="Version used in artifact names")
    parser.add_argument(
        "--release-dir",
        default=str(DIST_RELEASE_DIR),
        help="Directory with apidev-<version>-macos-<arch>.tar.gz files",
    )
    parser.add_argument(
        "--asset-base-url",
        required=True,
        help="Base URL used by formula for release artifact download",
    )
    parser.add_argument("--repo-owner", required=True, help="GitHub repository owner")
    parser.add_argument("--repo-name", default="apidev", help="GitHub repository name")
    parser.add_argument("--formula-name", default="apidev", help="Homebrew formula/binary name")
    parser.add_argument("--formula-class-name", default="Apidev", help="Ruby class name")
    parser.add_argument("--output", required=True, help="Target formula file path")
    parser.add_argument(
        "--default-arch",
        default=detect_arch(),
        help="Fallback arch when one binary exists",
    )
    args = parser.parse_args()

    release_dir = Path(args.release_dir).resolve()
    output_path = Path(args.output).resolve()

    artifacts_by_arch = collect_macos_artifacts(args.version, release_dir)
    formula = render_formula(
        version=args.version,
        formula_class_name=args.formula_class_name,
        repo_owner=args.repo_owner,
        repo_name=args.repo_name,
        formula_name=args.formula_name,
        asset_base_url=args.asset_base_url,
        artifacts_by_arch=artifacts_by_arch,
        default_arch=normalize_arch(args.default_arch),
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(formula, encoding="utf-8")
    print(f"Generated formula: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
