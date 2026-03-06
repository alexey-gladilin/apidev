# Phase 02: Release Publishing Surface and Homebrew Path

## Цель
Сделать release-процесс прозрачным для maintainers и пользователей, а optional Homebrew publish path безопасным и управляемым.

## Зависимости фазы
- Входы: артефакты `Phase 01`, `artifacts/design/02-behavior.md`, `artifacts/design/03-decisions.md`, `specs/release-automation/spec.md`.
- Блокирующие зависимости: завершенный workflow contract из `Phase 01`.
- Выходы фазы являются входом для `Phase 03`.

## Scope
- Обновить process docs с явным release checklist и quality gates.
- Добавить в `README.md` раздел Distribution с источником binary artifacts и базовыми install instructions.
- Добавить optional Homebrew publish как отдельную secret-gated job.

## Output Artifacts
- `docs/process/release*.md`
- `README.md`
- `.github/workflows/release*.yml`
- `scripts/release/*` (если требуется логика Homebrew path)

## Verification
- `make docs-check`
- проверка ссылок и целостности markdown-документации
- негативный прогон Homebrew path без секрета (controlled failure)
- позитивный прогон Homebrew path с валидным секретом в защищенном окружении

## Definition of Done
- Release checklist покрывает шаги `version/tag/build/smoke/publish` и ссылается на проверяемые CI jobs/команды.
- `README.md` содержит актуальную секцию Distribution с путями получения бинарников.
- Homebrew path изолирован, требует валидный секрет и не создает partial publish при ошибке pre-check.

## Риски
- Несоответствие документации фактическим CI шагам приведет к ручным ошибкам релиза.
- Неверные permissions/secret scope для Homebrew могут блокировать publish даже при валидной конфигурации workflow.
- Смешение core publish и Homebrew ветки увеличит blast radius ошибок.

## Rollback Notes
- При регрессии документации вернуть предыдущие версии `README`/`docs/process` в отдельном rollback PR.
- При нестабильном Homebrew path временно отключить соответствующую job feature-flag условием в workflow.
- Если Homebrew steps влияют на core publish, вынести их в полностью независимый workflow до стабилизации.
