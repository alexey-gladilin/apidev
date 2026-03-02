import json
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
    def write(self, generated_root: Path, target: Path, content: str) -> None:
        _ = (generated_root, target, content)

    def remove(self, generated_root: Path, target: Path) -> bool:
        _ = (generated_root, target)
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


def _create_service(
    monkeypatch,
    tmp_path: Path,
    *,
    changes: list[PlannedChange] | None = None,
) -> GenerateService:
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
        generated_root=tmp_path / ".apidev" / "output" / "api",
        changes=changes or [],
    )
    monkeypatch.setattr(service.diff_service, "run", lambda *args, **kwargs: plan)
    return service


def test_generate_apply_auto_creates_release_state_when_missing_and_git_baseline_resolves(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _write_project_config(tmp_path)
    service = _create_service(monkeypatch, tmp_path)

    monkeypatch.setattr(service, "_run_git_command", lambda *args, **kwargs: "a" * 40)

    result = service.run(tmp_path, check=False)

    release_state_path = tmp_path / ".apidev" / "release-state.json"
    assert release_state_path.exists()

    payload = json.loads(release_state_path.read_text(encoding="utf-8"))
    assert payload == {"release_number": 1, "baseline_ref": "a" * 40}
    assert result.drift_status == "no-drift"


def test_generate_apply_returns_baseline_missing_and_does_not_create_release_state_when_unresolved(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _write_project_config(tmp_path)
    service = _create_service(monkeypatch, tmp_path)

    monkeypatch.setattr(service, "_run_git_command", lambda *args, **kwargs: None)

    result = service.run(tmp_path, check=False)

    release_state_path = tmp_path / ".apidev" / "release-state.json"
    assert not release_state_path.exists()
    assert result.drift_status == "error"
    assert [diagnostic.code for diagnostic in result.diagnostics] == ["config.baseline-missing"]


def test_generate_apply_returns_deterministic_diagnostic_when_git_missing(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _write_project_config(tmp_path)
    service = _create_service(monkeypatch, tmp_path)

    def _raise_missing_git(*args, **kwargs):
        _ = (args, kwargs)
        raise FileNotFoundError("git not found")

    monkeypatch.setattr(subprocess, "run", _raise_missing_git)

    result = service.run(tmp_path, check=False)

    release_state_path = tmp_path / ".apidev" / "release-state.json"
    assert not release_state_path.exists()
    assert result.drift_status == "error"
    assert [diagnostic.code for diagnostic in result.diagnostics] == ["config.baseline-missing"]


def test_generate_apply_bumps_release_number_when_add_update_or_remove_applied(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _write_project_config(tmp_path)
    release_state_path = tmp_path / ".apidev" / "release-state.json"
    release_state_path.write_text(
        json.dumps({"release_number": 7, "baseline_ref": "v1.2.3"}),
        encoding="utf-8",
    )
    service = _create_service(
        monkeypatch,
        tmp_path,
        changes=[
            PlannedChange(path=Path("users.py"), content="x", change_type="ADD"),
            PlannedChange(path=Path("orders.py"), content="x", change_type="UPDATE"),
            PlannedChange(path=Path("legacy.py"), content="", change_type="REMOVE"),
        ],
    )

    service.run(tmp_path, check=False)

    payload = json.loads(release_state_path.read_text(encoding="utf-8"))
    assert payload["release_number"] == 8
    assert payload["baseline_ref"] == "v1.2.3"


def test_generate_apply_does_not_bump_release_number_on_noop_plan(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _write_project_config(tmp_path)
    release_state_path = tmp_path / ".apidev" / "release-state.json"
    release_state_path.write_text(
        json.dumps({"release_number": 4, "baseline_ref": "v1.2.3"}),
        encoding="utf-8",
    )
    service = _create_service(
        monkeypatch,
        tmp_path,
        changes=[PlannedChange(path=Path("users.py"), content="x", change_type="SAME")],
    )

    service.run(tmp_path, check=False)

    payload = json.loads(release_state_path.read_text(encoding="utf-8"))
    assert payload["release_number"] == 4


def test_generate_apply_baseline_ref_precedence_syncs_cli_override_before_release_state(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _write_project_config(tmp_path)
    release_state_path = tmp_path / ".apidev" / "release-state.json"
    release_state_path.write_text(
        json.dumps({"release_number": 2, "baseline_ref": "v1.0.0"}),
        encoding="utf-8",
    )
    service = _create_service(
        monkeypatch,
        tmp_path,
        changes=[PlannedChange(path=Path("users.py"), content="x", change_type="ADD")],
    )
    monkeypatch.setattr(service, "_run_git_command", lambda *args, **kwargs: "b" * 40)

    service.run(tmp_path, check=False, baseline_ref="v2.0.0")

    payload = json.loads(release_state_path.read_text(encoding="utf-8"))
    assert payload["baseline_ref"] == "v2.0.0"
    assert payload["release_number"] == 3


def test_generate_apply_baseline_ref_precedence_keeps_release_state_before_git_fallback(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _write_project_config(tmp_path)
    release_state_path = tmp_path / ".apidev" / "release-state.json"
    release_state_path.write_text(
        json.dumps({"release_number": 3, "baseline_ref": "v1.5.0"}),
        encoding="utf-8",
    )
    service = _create_service(
        monkeypatch,
        tmp_path,
        changes=[PlannedChange(path=Path("users.py"), content="x", change_type="ADD")],
    )
    monkeypatch.setattr(service, "_run_git_command", lambda *args, **kwargs: "c" * 40)

    service.run(tmp_path, check=False)

    payload = json.loads(release_state_path.read_text(encoding="utf-8"))
    assert payload["baseline_ref"] == "v1.5.0"
    assert payload["release_number"] == 4


def test_generate_apply_release_state_keeps_pre_run_payload_when_second_release_state_write_fails(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _write_project_config(tmp_path)
    release_state_path = tmp_path / ".apidev" / "release-state.json"
    pre_run_payload = {"release_number": 3, "baseline_ref": "v1.0.0"}
    release_state_path.write_text(json.dumps(pre_run_payload), encoding="utf-8")
    service = _create_service(
        monkeypatch,
        tmp_path,
        changes=[PlannedChange(path=Path("users.py"), content="x", change_type="ADD")],
    )

    original_write_text = service.fs.write_text

    def _fail_on_bump_write(path: Path, content: str) -> None:
        if path == release_state_path and '"release_number": 4' in content:
            raise OSError("simulated release-state write failure")
        original_write_text(path, content)

    monkeypatch.setattr(service.fs, "write_text", _fail_on_bump_write)

    result = service.run(tmp_path, check=False, baseline_ref="v2.0.0")

    assert result.drift_status == "error"
    payload = json.loads(release_state_path.read_text(encoding="utf-8"))
    assert payload == pre_run_payload
