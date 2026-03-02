## ADDED Requirements

### Requirement: Multi-OS release pipeline for standalone CLI binary
Система SHALL предоставлять автоматизированный release pipeline для публикации standalone binary `apidev` под `macOS`, `Windows`, `Linux`.

#### Scenario: Release trigger starts multi-OS build
- **WHEN** в GitHub создается release со статусом `published`
- **THEN** pipeline SHALL запускать сборку бинарника на matrix runners `macOS`, `Windows`, `Linux`
- **AND** pipeline SHALL поддерживать ручной запуск через `workflow_dispatch`

#### Scenario: Binary smoke checks gate artifact publication
- **WHEN** бинарник собран для целевой ОС
- **THEN** pipeline SHALL выполнять smoke-check запуска `apidev --help`
- **AND** при провале smoke-check pipeline SHALL NOT публиковать release assets

#### Scenario: Release assets are published deterministically
- **WHEN** все обязательные проверки pipeline завершены успешно
- **THEN** pipeline SHALL публиковать бинарные артефакты в GitHub Releases
- **AND** именование артефактов SHALL быть детерминированным по схеме `apidev-<version>-<os>-<arch>`

### Requirement: Release process documentation and quality gates
Система SHALL документировать release flow и обязательные quality gates как repository-wide процесс.

#### Scenario: Distribution surface is documented
- **WHEN** пользователь открывает `README.md`
- **THEN** documentation SHALL содержать раздел Distribution с источником binary artifacts и базовыми install instructions

#### Scenario: Release checklist is explicit and test-backed
- **WHEN** maintainers выполняют release
- **THEN** process docs SHALL описывать обязательные шаги version/tag/build/smoke/publish
- **AND** quality gates SHALL быть привязаны к проверяемым командам/джобам CI

### Requirement: Optional Homebrew publication path
Система SHALL поддерживать автоматизированный publish Homebrew formula как отдельный опциональный release path.

#### Scenario: Homebrew publish is secret-gated
- **WHEN** release pipeline запускает Homebrew publish job
- **THEN** job SHALL требовать валидный секрет токена для tap-репозитория
- **AND** при отсутствии секрета job SHALL завершаться контролируемой ошибкой без partial publish
