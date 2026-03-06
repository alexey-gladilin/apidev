# Change: Рефакторинг структуры `.apidev/config.toml`

## Почему
Текущая структура конфигурации содержит смешение семантик путей и доменных настроек, что усложняет поддержку и дальнейшее расширение конфигурационного контракта.

## Что меняется
- Вводится единая структурная модель секций конфига по смысловым зонам (`paths`, `inputs`, `generator`, `evolution`, `openapi`).
- Убирается поле `version` из конфигурационного контракта.
- Фиксируется правило fail-fast: поддерживается только новый формат конфига без backward compatibility.
- Уточняется контракт валидации путей и обязательных полей для генерации и release-state.
- Обновляются `apidev init`, документация и тестовые контракты под новый формат.

## Целевая структура конфигурации (план реализации)
```toml
[paths]
templates_dir = ".apidev/templates"
release_state_file = ".apidev/release-state.json"

[inputs]
contracts_dir = ".apidev/contracts"
shared_models_dir = ".apidev/models"

[generator]
generated_dir = ".apidev/output/api"
postprocess = "auto"
scaffold = true
scaffold_dir = ".apidev/integration"
scaffold_write_policy = "create-missing"

[evolution]
compatibility_policy = "warn"
grace_period_releases = 2

[openapi]
include_extensions = true
```

## Влияние
- Affected specs: `config` (new).
- Affected code:
  - `src/apidev/core/models/config.py`
  - `src/apidev/infrastructure/config/toml_loader.py`
  - `src/apidev/commands/init_cmd.py`
  - `tests/**` (config loader, init, integration)
  - `docs/reference/configuration.md` (или эквивалентный конфигурационный документ)

## Ограничения и рамки
- Изменение охватывает только `apidev`.
- В proposal-фазе production-код не изменяется.

## Linked Artifacts
- Research: `artifacts/research/2026-03-06-config-refactor-baseline.md`
- Design:
  - `artifacts/design/README.md`
  - `artifacts/design/01-architecture.md`
  - `artifacts/design/02-behavior.md`
  - `artifacts/design/03-decisions.md`
  - `artifacts/design/04-testing.md`
- Plan:
  - `artifacts/plan/README.md`
  - `artifacts/plan/phase-01.md`
  - `artifacts/plan/phase-02.md`
  - `artifacts/plan/phase-03.md`
  - `artifacts/plan/implementation-handoff.md`
