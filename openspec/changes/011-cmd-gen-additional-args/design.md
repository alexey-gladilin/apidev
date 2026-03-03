## Контекст
`apidev gen` уже поддерживает дополнительные флаги (`--scaffold`, `--no-scaffold`, `--compatibility-policy`, `--baseline-ref`), но не имеет механизма выборочной генерации endpoint-ов.
Текущий pipeline строит план генерации по полному списку операций, загруженных из всех YAML-контрактов.

## Цели / Не-цели
- Цели:
  - добавить CLI-контракт include/exclude фильтров для endpoint-ов в `apidev gen`;
  - сохранить детерминированность generation-plan и существующие safety-гарантии;
  - добавить проверяемые diagnostics для невалидных фильтров и пустого результата фильтрации.
- Не-цели:
  - изменение формата контрактов YAML;
  - изменение semantics `apidev diff` в рамках этого change;
  - изменение compatibility/release-state policy.

## Решения
- Добавить в `apidev gen` два множественных флага:
  - `--include-endpoint <pattern>`;
  - `--exclude-endpoint <pattern>`.
- Применять фильтрацию к operation selection до построения generation plan:
  - include: whitelist (если задан);
  - exclude: blacklist поверх include/full-set.
- Поддержать deterministic matching policy для endpoint pattern:
  - pattern трактуется как case-sensitive glob;
  - match по `operation_id` и `contract_relpath` (логика `OR`);
  - невалидные pattern: пустая строка и malformed glob syntax (включая незакрытый `[` character-class);
  - фиксированная нормализация и порядок применения фильтров.
- Возвращать диагностируемые ошибки для:
  - невалидного pattern;
  - empty effective set после фильтрации.
  - namespace кодов диагностики: `generation.*` (согласно taxonomy capability `009-diagnostics-contract`).
  - diagnostics payload обязан включать `code`, `location`, `detail`.

## Риски / Компромиссы
- Риск: пользователь может ожидать фильтрацию и в `apidev diff`.
  - Митигация: явно зафиксировать scope текущего change как `apidev gen` only.
- Риск: фильтрация может создать неочевидный remove-план при частичной генерации.
  - Митигация: stale-remove ограничивается только effective endpoint set; endpoint-ы вне scope фильтрованного запуска не участвуют в remove-плане только из-за отсутствия в фильтре.
- Риск: неоднозначность шаблонов фильтра (glob/regex).
  - Митигация: зафиксировать glob-only policy в spec/design и добавить негативные тесты на malformed glob.

## Linked Artifacts
- Research: [artifacts/research/2026-03-03-endpoint-filtering-baseline.md](./artifacts/research/2026-03-03-endpoint-filtering-baseline.md)
- Design package index: [artifacts/design/README.md](./artifacts/design/README.md)
- Architecture: [artifacts/design/01-architecture.md](./artifacts/design/01-architecture.md)
- Behavior: [artifacts/design/02-behavior.md](./artifacts/design/02-behavior.md)
- Decisions: [artifacts/design/03-decisions.md](./artifacts/design/03-decisions.md)
- Testing: [artifacts/design/04-testing.md](./artifacts/design/04-testing.md)
- Plan package: [artifacts/plan/README.md](./artifacts/plan/README.md)
- Spec delta: [specs/cli-tool-architecture/spec.md](./specs/cli-tool-architecture/spec.md)

## Готовность к Implement
После approval этот change-пакет является входом для отдельной implement-команды.
