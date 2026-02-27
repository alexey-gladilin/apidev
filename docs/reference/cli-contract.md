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
- `1` — бизнес-ошибка, validation failure, drift, invalid input на уровне домена;
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
