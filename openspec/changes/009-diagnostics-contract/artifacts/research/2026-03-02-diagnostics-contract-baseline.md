# Baseline Research: Diagnostics Contract (2026-03-02)

## Scope
- Анализ текущего diagnostics-поведения для команд `apidev validate`, `apidev diff`, `apidev gen --check`, `apidev gen`.
- Анализ текущих DTO/моделей diagnostics в application/core слоях.
- Фиксация расхождений относительно цели Horizon 1 (`docs/roadmap.md`).

## Evidence

### 1) `validate` уже имеет machine-readable режим
- `src/apidev/commands/validate_cmd.py`:
  - поддерживает флаг `--json`;
  - в JSON выводит payload с `diagnostics` и `summary`;
  - diagnostics строятся через `ValidationDiagnostic.as_dict()`.

### 2) `diff` и `gen` не имеют паритетного JSON-контракта
- `src/apidev/commands/diff_cmd.py`:
  - отсутствует `--json` флаг;
  - выводит текстовые строки (`No changes`, `Drift status: ...`, `COMPATIBILITY_* ...`).
- `src/apidev/commands/generate_cmd.py`:
  - отсутствует `--json` флаг;
  - выводит текстовые строки (`Drift detected`, `Generation failed`, `Applied changes: ...`).

### 3) Диагностические модели различаются по форме
- `src/apidev/core/models/diagnostic.py`:
  - `ValidationDiagnostic` поля: `code`, `severity`, `message`, `location`, `rule`.
- `src/apidev/application/dto/generation_plan.py`:
  - `GenerationDiagnostic` поля: `code`, `location`, `detail`;
  - `CompatibilityDiagnostic` поля: `category`, `code`, `location`, `detail`.

### 4) Compatibility diagnostics уже участвуют в CLI, но только как text output
- `src/apidev/commands/common/compatibility.py`:
  - печатает `Compatibility policy`, `Compatibility overall`, `COMPATIBILITY_<CATEGORY> ...`.
- Структурированная сериализация compatibility diagnostics в JSON отсутствует.

### 5) Нормативные документы фиксируют semantics, но не единый JSON envelope для всех режимов
- `docs/reference/cli-contract.md`:
  - описывает exit semantics, drift-status, compatibility policy;
  - не задает единый machine-readable JSON контракт для `diff`/`gen`.
- `docs/roadmap.md` (Horizon 1):
  - формулирует цель унификации machine-readable сигналов для всех ключевых режимов CLI.

### 6) Тестовый контур уже покрывает часть diagnostics/determinism, но не cross-command JSON parity
- `tests/unit/test_validate_cmd.py` проверяет JSON для validate;
- `tests/integration/test_compatibility_policy_cli.py` проверяет compatibility/drift в основном через CLI text output;
- кросс-командный контрактный JSON-набор для `validate/diff/gen` не обнаружен.

## Observed Gaps (fact summary)
- JSON-режим контрактно определен для `validate`, но не для `diff`/`gen`.
- Поля diagnostics между validate/generation/compatibility не выровнены.
- Единый envelope и namespace-политика codes не зафиксированы в текущем OpenSpec change-контексте.
