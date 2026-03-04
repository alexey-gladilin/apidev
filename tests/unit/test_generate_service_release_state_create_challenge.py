from pathlib import Path
from typing import cast
import subprocess

from apidev.application.dto.generation_plan import GenerationPlan, PlannedChange
from apidev.application.services.generate_service import GenerateService
from apidev.core.ports.contract_loader import ContractLoaderPort
from apidev.core.ports.filesystem import FileSystemPort
from apidev.core.ports.python_postprocessor import PythonPostprocessorPort
from apidev.core.ports.template_engine import TemplateEnginePort
from apidev.infrastructure.config.toml_loader import TomlConfigLoader
from apidev.infrastructure.filesystem.local_fs import LocalFileSystem


class _NoopWriter:
    def write(self, generated_dir_path: Path, target: Path, content: str) -> None:
        _ = (generated_dir_path, target, content)

    def remove(self, generated_dir_path: Path, target: Path) -> bool:
        _ = (generated_dir_path, target)
        return True


def _write_project_config(project_dir: Path) -> None:
    (project_dir / ".apidev").mkdir(parents=True, exist_ok=True)
    (project_dir / ".apidev" / "config.toml").write_text(
        """
version = "1"

[contracts]
dir = ".apidev/contracts"

[generator]
generated_dir = ".apidev/output/api"

[templates]
dir = ".apidev/templates"

[evolution]
release_state_file = ".apidev/release-state.json"
""".strip(),
        encoding="utf-8",
    )


def _create_service(monkeypatch, tmp_path: Path) -> GenerateService:
    fs = LocalFileSystem()
    service = GenerateService(
        config_loader=TomlConfigLoader(fs=fs),
        loader=cast(ContractLoaderPort, object()),
        renderer=cast(TemplateEnginePort, object()),
        fs=cast(FileSystemPort, fs),
        writer=_NoopWriter(),
        postprocessor=cast(PythonPostprocessorPort, object()),
    )
    plan = GenerationPlan(generated_dir_path=tmp_path / ".apidev" / "output" / "api", changes=[])
    monkeypatch.setattr(service.diff_service, "run", lambda *args, **kwargs: plan)
    return service


def test_generate_apply_does_not_create_release_state_with_empty_baseline_ref(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _write_project_config(tmp_path)
    service = _create_service(monkeypatch, tmp_path)

    result = service.run(tmp_path, check=False, baseline_ref="")

    release_state_path = tmp_path / ".apidev" / "release-state.json"
    assert not release_state_path.exists()
    assert result.drift_status == "error"
    assert [diagnostic.code for diagnostic in result.diagnostics] == ["config.baseline-invalid"]


def test_generate_apply_does_not_create_release_state_with_out_of_range_sha_lengths(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _write_project_config(tmp_path)
    service = _create_service(monkeypatch, tmp_path)

    first_result = service.run(tmp_path, check=False, baseline_ref="a" * 6)
    release_state_path = tmp_path / ".apidev" / "release-state.json"
    assert not release_state_path.exists()
    assert first_result.drift_status == "error"
    assert [diagnostic.code for diagnostic in first_result.diagnostics] == [
        "config.baseline-invalid"
    ]

    second_result = service.run(tmp_path, check=False, baseline_ref="a" * 41)
    assert not release_state_path.exists()
    assert second_result.drift_status == "error"
    assert [diagnostic.code for diagnostic in second_result.diagnostics] == [
        "config.baseline-invalid"
    ]


def test_generate_apply_does_not_crash_or_overwrite_invalid_release_state_json_on_bump(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _write_project_config(tmp_path)
    release_state_path = tmp_path / ".apidev" / "release-state.json"
    release_state_path.write_text("{invalid-json", encoding="utf-8")
    fs = LocalFileSystem()
    service = GenerateService(
        config_loader=TomlConfigLoader(fs=fs),
        loader=cast(ContractLoaderPort, object()),
        renderer=cast(TemplateEnginePort, object()),
        fs=cast(FileSystemPort, fs),
        writer=_NoopWriter(),
        postprocessor=cast(PythonPostprocessorPort, object()),
    )
    plan = GenerationPlan(
        generated_dir_path=tmp_path / ".apidev" / "output" / "api",
        changes=[PlannedChange(path=Path("users.py"), content="x", change_type="ADD")],
    )
    monkeypatch.setattr(service.diff_service, "run", lambda *args, **kwargs: plan)
    monkeypatch.setattr(service, "_run_git_command", lambda *args, **kwargs: None)

    result = service.run(tmp_path, check=False)

    assert result.drift_status == "error"
    assert [diagnostic.code for diagnostic in result.diagnostics] == ["config.baseline-invalid"]
    assert release_state_path.read_text(encoding="utf-8") == "{invalid-json"


def test_generate_apply_returns_baseline_invalid_when_git_missing_and_release_state_invalid(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _write_project_config(tmp_path)
    release_state_path = tmp_path / ".apidev" / "release-state.json"
    release_state_path.write_text("{invalid-json", encoding="utf-8")
    service = _create_service(monkeypatch, tmp_path)

    def _raise_missing_git(*args, **kwargs):
        _ = (args, kwargs)
        raise FileNotFoundError("git not found")

    monkeypatch.setattr(subprocess, "run", _raise_missing_git)

    result = service.run(tmp_path, check=False)

    assert result.drift_status == "error"
    assert [diagnostic.code for diagnostic in result.diagnostics] == ["config.baseline-invalid"]
    assert release_state_path.read_text(encoding="utf-8") == "{invalid-json"
