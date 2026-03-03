# apidev

Binary CLI tool for contract-driven API scaffolding.

## Commands

- `apidev init`
- `apidev validate`
- `apidev diff`
- `apidev gen`

Compatibility alias:
- `apidev generate` (legacy alias for `apidev gen`)

## Endpoint фильтры для `gen`

`apidev gen` поддерживает repeatable-флаги:
- `--include-endpoint <pattern>`
- `--exclude-endpoint <pattern>`

Фильтрация всегда применяется по правилу `include -> exclude`, где pattern — case-sensitive glob по `operation_id` и `contract_relpath`.

## Docs

- `docs/README.md` — documentation map and source-of-truth index.
- `docs/roadmap.md` — historical roadmap snapshot and planned direction.
- `docs/process/ai-workflow.md` — AI workflow, agents, and operational guidance.

## Дистрибуция

Готовые standalone-бинарники публикуются в GitHub Releases:
- Путь: `https://github.com/alexey-gladilin/apidev/releases/latest`
- Ассеты: `apidev-<version>-<os>-<arch>.zip` (Windows) или `apidev-<version>-<os>-<arch>.tar.gz` (Linux/macOS)

Как получить бинарник:
1. Откройте страницу latest release.
2. Скачайте архив под вашу платформу из секции Assets.
3. Распакуйте архив и добавьте `apidev` (или `apidev.exe` на Windows) в `PATH`.
