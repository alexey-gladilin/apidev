# CLI Контракт APIDev

Статус: `Authoritative`

Этот документ задает проверяемый контракт CLI и используется как единый источник истины для PR review, тестов и изменений help/UX.

## Канонические команды

Набор верхнего уровня:

- `apidev init`
- `apidev validate`
- `apidev diff`
- `apidev gen`

Каноническая команда генерации:

- `apidev gen`

Compatibility alias:

- `apidev generate`

Во всех нормативных документах, walkthroughs и примерах должна использоваться команда `apidev gen`. Алиас `apidev generate` упоминается только как compatibility mechanism.

## Контракт структуры generated output

Каноническая структура generated output для `apidev diff`/`apidev gen` — domain-first:

```text
<generated_dir>/
├── operation_map.py
├── openapi_docs.py
└── <domain>/
    ├── routes/
    │   └── <operation>.py
    └── models/
        ├── <operation>_request.py
        ├── <operation>_response.py
        └── <operation>_error.py
```

Здесь `<generated_dir>` определяется через `generator.generated_dir` в `.apidev/config.toml`.

## Контракт scaffold-флагов

Для `apidev gen` и `apidev diff` поддерживаются CLI overrides:

- `--scaffold` — включить генерацию integration scaffold в текущем запуске;
- `--no-scaffold` — отключить генерацию integration scaffold в текущем запуске.

Правила:

- если ни один флаг не указан, используется `generator.scaffold` из `.apidev/config.toml`;
- при указании флага CLI имеет приоритет над config;
- scaffold-файлы создаются только в режиме `create-if-missing` (существующие не перезаписываются).

## Контракт help и UX

Обязательные требования:

- каждый уровень команды поддерживает `-h` и `--help`;
- root help содержит секции `Usage`, `Options`, `Commands`;
- у каждой команды есть краткое и однозначное описание;
- ожидаемые пользовательские ошибки выводятся без traceback;
- формулировки ошибок пригодны для CI-логов и дают следующий шаг, если это применимо.

## Контракт совместимости

Правила алиасов:

- скрытый алиас сохраняется минимум на один минорный релиз после переименования;
- каноническое имя и алиасы должны быть отражены в документации;
- удаление алиаса возможно только после явного периода депрекации.

Текущий alias policy:

- `apidev gen` — canonical command
- `apidev generate` — hidden compatibility alias

## Контракт кодов выхода

- `0` — успешное выполнение;
- `1` — бизнес-ошибка, validation failure, blocking drift (например, `gen --check`), invalid input на уровне домена;
- `2` — ошибка парсинга CLI или неверной сигнатуры команды.

## Контракт drift-status и exit semantics

Нормализованные drift-статусы:

- `drift` — обнаружены изменения относительно generated artifacts;
- `no-drift` — изменения не обнаружены или успешно применены;
- `error` — ошибка pipeline (включая validation/business failure).

Матрица режимов:

- `apidev diff`
  - `drift` -> exit `0` (read-only preview);
  - `no-drift` -> exit `0`;
  - `error` -> exit `1`.
- `apidev gen --check`
  - `drift` -> exit `1` (CI gate);
  - `no-drift` -> exit `0`;
  - `error` -> exit `1`.
- `apidev gen`
  - successful apply / no changes -> `no-drift`, exit `0`;
  - `error` -> exit `1`.

Правило для remove-only сценариев:

- `remove-only` изменения считаются `drift`;
- для `apidev diff` это informational drift с exit `0` (если не сработал compatibility policy gate);
- для `apidev gen --check` это blocking drift с exit `1`.

## Контракт compatibility policy и baseline

- `--compatibility-policy` поддерживает значения `warn` (по умолчанию) и `strict`.
- В `warn` команда выводит compatibility diagnostics, но не фейлит запуск только из-за policy.
- В `strict` команда завершает выполнение с `exit 1`, если итоговая compatibility-категория `breaking`.
- `--baseline-ref` (git tag/commit) переопределяет `baseline_ref` из release-state.
- Baseline precedence для compare/apply: `CLI --baseline-ref -> release-state.baseline_ref -> git HEAD`.
- При отсутствии baseline или невалидном baseline используются diagnostics `baseline-missing` и `baseline-invalid`.
- При применении baseline выводится diagnostic `baseline-ref-applied` с деталями источника (`cli` или `release-state`).

## Контракт release-state lifecycle в `gen apply`

- `apidev diff` и `apidev gen --check` не пишут release-state (strict read-only).
- `apidev gen` (без `--check`) — единственный CLI-режим, где разрешены create/sync/bump операции release-state.
- Auto-create: если release-state отсутствует, `gen apply` создает его с `release_number=1` и resolved `baseline_ref` (по precedence).
- `fail-without-write`: если baseline не удалось резолвить/валидировать, `gen apply` завершается с `error` (`baseline-missing` или `baseline-invalid`) до release-state записи.
- Bump semantics: `release_number` увеличивается ровно на `1` только при реально примененных drift-изменениях (`ADD|UPDATE|REMOVE`) и только если release-state существовал до запуска apply.
- Если изменений нет, bump не выполняется.
- При ошибке записи release-state команда завершается с `error` и diagnostic `release-state-apply-failed`, а release-state откатывается к pre-run состоянию.

## Контракт deprecation semantics

- APIDev использует lifecycle `active -> deprecated -> removed`.
- Для `diff` и `gen --check` удаление operation до конца grace window классифицируется как `deprecation-window-violation` (breaking).
- Если grace window соблюдено, выводится `deprecation-window-satisfied` (non-breaking).
- Статус deprecation должен быть отражен в generated metadata/artifacts.

## Минимальные тесты для любого CLI-изменения

- тест на root help;
- тест на help хотя бы одной подкоманды;
- тест доступности канонической команды `gen`;
- если затрагивается алиас, тест, что alias ведет к тому же поведению;
- если затрагиваются ошибки, тест на соответствующий exit code и сообщение.

Рекомендуемая команда запуска:

- `uv run pytest tests/unit/test_cli_conventions.py`

## PR checklist для CLI-изменений

- [ ] Обновлены help-описания команд.
- [ ] Поддерживаются `-h` и `--help`.
- [ ] Не сломана команда `apidev gen`.
- [ ] Compatibility alias отражен в документации, если он менялся.
- [ ] Обновлены или добавлены CLI-тесты.

## Связанные документы

- `docs/process/testing-strategy.md`
- `docs/reference/glossary.md`
- `docs/architecture/architecture-overview.md`
- `docs/architecture/generated-integration.md`
