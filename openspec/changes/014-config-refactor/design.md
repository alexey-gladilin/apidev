## Контекст
Рефакторинг нацелен на формализацию конфигурационного контракта `apidev` вокруг четкой секционной модели без legacy-веток парсинга.

## Цели
- Согласовать нейминг секций и ключей по смысловым зонам.
- Упростить валидацию и диагностику ошибок конфигурации.
- Исключить неоднозначность интерпретации путей.

## Не-цели
- Добавление новых пользовательских CLI-фич вне конфигурационного контракта.
- Поддержка старых ключей и миграционных fallback-стратегий.

## Нормативная структура, подлежащая реализации
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

## Явные зависимости от канонических capabilities
- `contract-evolution-integration` (MODIFIED): путь к release state переопределяется только через `evolution.release_state_file` в `.apidev/config.toml`; read-only команды используют этот путь консистентно и не мутируют release state.
- `config` (ADDED): вводит канонический набор секций/ключей, deterministic fail-fast валидацию unknown sections/keys и детерминированные diagnostics для path resolution.

## Linked Artifacts
- Research: `artifacts/research/2026-03-06-config-refactor-baseline.md`
- Design package:
  - `artifacts/design/README.md`
  - `artifacts/design/01-architecture.md`
  - `artifacts/design/02-behavior.md`
  - `artifacts/design/03-decisions.md`
  - `artifacts/design/04-testing.md`
