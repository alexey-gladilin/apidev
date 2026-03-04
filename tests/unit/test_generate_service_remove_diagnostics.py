from pathlib import Path
from typing import cast

from apidev.application.dto.generation_plan import GenerationPlan, PlannedChange
from apidev.application.services.generate_service import GenerateService
from apidev.core.ports.config_loader import ConfigLoaderPort
from apidev.core.ports.contract_loader import ContractLoaderPort
from apidev.core.ports.filesystem import FileSystemPort
from apidev.core.ports.python_postprocessor import PythonPostprocessorPort
from apidev.core.ports.template_engine import TemplateEnginePort


class _NoopWriter:
    def write(self, generated_dir_path: Path, target: Path, content: str) -> None:
        _ = (generated_dir_path, target, content)

    def remove(self, generated_dir_path: Path, target: Path) -> bool:
        _ = (generated_dir_path, target)
        return True


def _create_service(monkeypatch, tmp_path: Path, remove_path: Path) -> GenerateService:
    service = GenerateService(
        config_loader=cast(ConfigLoaderPort, object()),
        loader=cast(ContractLoaderPort, object()),
        renderer=cast(TemplateEnginePort, object()),
        fs=cast(FileSystemPort, object()),
        writer=_NoopWriter(),
        postprocessor=cast(PythonPostprocessorPort, object()),
    )
    plan = GenerationPlan(
        generated_dir_path=tmp_path / ".apidev" / "output" / "api",
        changes=[PlannedChange(path=remove_path, content="", change_type="REMOVE")],
    )
    monkeypatch.setattr(service.diff_service, "run", lambda *args, **kwargs: plan)
    return service


def test_generate_service_remove_conflict_returns_error_with_machine_readable_diagnostic(
    tmp_path: Path,
    monkeypatch,
) -> None:
    remove_path = tmp_path / ".apidev" / "output" / "api" / "routers" / "stale.py"
    service = _create_service(monkeypatch, tmp_path, remove_path)

    monkeypatch.setattr(
        service, "_remove_generated_artifact", lambda generated_dir_path, target: False
    )

    result = service.run(tmp_path, baseline_ref="v1.0.0")

    assert result.drift_status == "error"
    assert len(result.diagnostics) == 1
    diagnostic = result.diagnostics[0]
    assert diagnostic.code == "generation.remove-conflict"
    assert diagnostic.location == remove_path.as_posix()
    assert "missing" in diagnostic.detail
    assert set(diagnostic.as_dict().keys()) == {"code", "location", "detail"}


def test_generate_service_remove_boundary_violation_returns_error_with_canonical_code(
    tmp_path: Path,
    monkeypatch,
) -> None:
    remove_path = tmp_path / ".apidev" / "output" / "api" / "routers" / "stale.py"
    service = _create_service(monkeypatch, tmp_path, remove_path)

    def _raise_boundary_error(generated_dir_path: Path, target: Path) -> bool:
        raise ValueError(f"Refusing to remove outside generated root: {target}")

    monkeypatch.setattr(service, "_remove_generated_artifact", _raise_boundary_error)

    result = service.run(tmp_path, baseline_ref="v1.0.0")

    assert result.drift_status == "error"
    assert len(result.diagnostics) == 1
    diagnostic = result.diagnostics[0]
    assert diagnostic.code == "generation.remove-boundary-violation"
    assert diagnostic.location == remove_path.as_posix()
    assert "outside generated root" in diagnostic.detail
    assert set(diagnostic.as_dict().keys()) == {"code", "location", "detail"}
