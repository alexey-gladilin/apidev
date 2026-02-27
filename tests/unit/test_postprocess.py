from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from apidev.infrastructure.output.postprocess import format_python_content, run_python_postprocess


def test_postprocess_none_mode_skips(tmp_path: Path) -> None:
    result = run_python_postprocess(
        project_dir=tmp_path,
        changed_paths=[tmp_path / "a.py"],
        mode="none",
    )

    assert result.status == "skipped"


def test_postprocess_auto_skips_when_no_formatter_found(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr("apidev.infrastructure.output.postprocess.shutil.which", lambda _: None)

    result = run_python_postprocess(
        project_dir=tmp_path,
        changed_paths=[tmp_path / "a.py"],
        mode="auto",
    )

    assert result.status == "skipped"
    assert "no formatter found" in result.message.lower()


def test_postprocess_auto_prefers_ruff(tmp_path: Path, monkeypatch) -> None:
    def _which(name: str) -> str | None:
        if name == "ruff":
            return "/usr/bin/ruff"
        return None

    captured: list[list[str]] = []

    def _run(cmd: list[str], **_: object) -> SimpleNamespace:
        captured.append(cmd)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("apidev.infrastructure.output.postprocess.shutil.which", _which)
    monkeypatch.setattr("apidev.infrastructure.output.postprocess.subprocess.run", _run)

    result = run_python_postprocess(
        project_dir=tmp_path,
        changed_paths=[tmp_path / "a.py", tmp_path / "b.txt"],
        mode="auto",
    )

    assert result.status == "applied"
    assert captured and captured[0][:2] == ["ruff", "format"]


def test_postprocess_explicit_formatter_fails_when_missing(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr("apidev.infrastructure.output.postprocess.shutil.which", lambda _: None)

    result = run_python_postprocess(
        project_dir=tmp_path,
        changed_paths=[tmp_path / "a.py"],
        mode="black",
    )

    assert result.status == "failed"
    assert "not installed" in result.message.lower()


def test_format_python_content_auto_returns_original_when_no_formatter(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr("apidev.infrastructure.output.postprocess.shutil.which", lambda _: None)
    source = "x=1\n"

    rendered = format_python_content(
        project_dir=tmp_path,
        target_path=tmp_path / "x.py",
        content=source,
        mode="auto",
    )

    assert rendered == source


def test_format_python_content_auto_formats_with_ruff(tmp_path: Path, monkeypatch) -> None:
    def _which(name: str) -> str | None:
        if name == "ruff":
            return "/usr/bin/ruff"
        return None

    def _run(cmd: list[str], **kwargs: object) -> SimpleNamespace:
        source = str(kwargs["input"])
        assert cmd[:2] == ["ruff", "format"]
        return SimpleNamespace(returncode=0, stdout="x = 1\n", stderr="")

    monkeypatch.setattr("apidev.infrastructure.output.postprocess.shutil.which", _which)
    monkeypatch.setattr("apidev.infrastructure.output.postprocess.subprocess.run", _run)

    rendered = format_python_content(
        project_dir=tmp_path,
        target_path=tmp_path / "x.py",
        content="x=1\n",
        mode="auto",
    )

    assert rendered == "x = 1\n"
