# Phase 01 — Контракт и спецификация

## Scope
- Зафиксировать каноническую структуру секций `.apidev/config.toml`.
- Зафиксировать нормативный набор ключей внутри каждой секции.
- Устранить неоднозначность по `release_state` через единый ключ `evolution.release_state_file`.

## Target Schema

```toml
[paths]
templates_dir = ".apidev/templates"

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
release_state_file = ".apidev/release-state.json"
compatibility_policy = "warn"
grace_period_releases = 2

[openapi]
include_extensions = true
```

## Canonical Sections
- `paths`
- `inputs`
- `generator`
- `evolution`
- `openapi`

## Canonical Keys
- `paths.templates_dir`
- `inputs.contracts_dir`
- `inputs.shared_models_dir`
- `generator.generated_dir`
- `generator.postprocess`
- `generator.scaffold`
- `generator.scaffold_dir`
- `generator.scaffold_write_policy`
- `evolution.release_state_file`
- `evolution.compatibility_policy`
- `evolution.grace_period_releases`
- `openapi.include_extensions`

## Contract Rules (Phase 01 Baseline)
- Поле `version` не входит в контракт и считается недопустимым ключом.
- Unknown sections/keys запрещены (fail-fast на этапе загрузки конфига).
- Все относительные пути резолвятся относительно `project_dir`.
- Проверка выхода пути за пределы `project_dir` выполняется после нормализации.
- Для `release_state` используется только `evolution.release_state_file`.

## Design-Review Checklist (Verification)
- [x] Набор секций полностью покрывает целевые зоны (`paths`, `inputs`, `generator`, `evolution`, `openapi`).
- [x] Каждый ключ однозначно закреплен за одной секцией и не дублируется.
- [x] `release_state` имеет единый источник истины: `evolution.release_state_file`.
- [x] Отсутствуют противоречия с `proposal.md` и `design.md` по структуре и неймингу.
- [x] Базовые fail-fast правила явно зафиксированы и непротиворечивы.

## Outputs
- `artifacts/plan/phase-01.md` (этот документ как согласованный baseline для Task 1.1).

## Verification
- `design-review` (документарная проверка согласованности схемы; запуск автоматических тестов не требуется на этой фазе).
