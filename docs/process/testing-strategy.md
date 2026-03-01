# Стратегия Тестирования APIDev

Статус: `Authoritative`

Этот документ задает тестовую политику проекта: что именно мы тестируем, на каких уровнях, какие сценарии обязательны и какие проверки считаются quality gate.

## Цель тестирования

Тестовая система APIDev должна подтверждать:

- корректность contract-driven pipeline;
- безопасность generated/manual boundary;
- соблюдение архитектурных ограничений;
- стабильность CLI-контракта;
- детерминированность генерации и drift detection.

## Что тестируем

- CLI contract и help/UX;
- загрузку и базовую валидацию контрактов;
- generation pipeline и diff behavior;
- write-boundary policy;
- архитектурные инварианты слоев и зависимостей;
- deterministic generation;
- конфигурационные пути и single source path policy.
- integration contract generated/manual (registry/factory, endpoint/auth/error/openapi wiring).

## Уровни тестирования

### Unit tests

Используются для проверки:

- локальной логики сервисов;
- доменных правил;
- отдельных DTO и вспомогательных функций;
- CLI поведения без filesystem-heavy сценариев.

### Contract tests

Используются для проверки проектных инвариантов и поведенческих контрактов pipeline.

### Integration tests

Используются для проверки end-to-end сценариев CLI/service pipeline на временном проекте.

### Architecture tests

Используются для автоматической защиты архитектурных правил.

## Generated/manual boundary policy

Обязательные проверки:

- `diff` не пишет файлы;
- `apidev gen --check` не пишет файлы;
- запись допускается только внутрь generated root;
- manual-код не должен перезаписываться генератором;
- одинаковый вход должен давать одинаковый generated output.

## CLI UX tests

Для любого изменения CLI обязательны минимум:

- root help тест;
- help тест хотя бы одной подкоманды;
- тест доступности канонической команды `gen`;
- тест compatibility alias, если он затрагивается;
- проверка кодов выхода, если меняется error handling.

## Минимальный набор тестов для изменения

### Если меняется CLI contract

- `tests/unit/test_cli_conventions.py`
- релевантные integration tests, если меняется пользовательский сценарий

### Если меняется architecture rule или layering

- `tests/unit/architecture/*`
- `tests/contract/architecture/*`

### Если меняется generation pipeline

- unit tests сервисов;
- contract tests pipeline/write-boundary;
- integration roundtrip tests;
- при необходимости drift-related regression tests.

### Если меняется integration contract generated/manual

- contract tests на структуру operation registry и metadata wiring (`router_module`, `models`, `bridge`);
- integration tests на runtime-сборку endpoint-ов через registry/factory pattern;
- integration tests на auth wiring (`public`/`bearer`) через manual dependencies;
- integration tests на error mapping wrapper и contract-compatible HTTP responses;
- integration tests на OpenAPI assembly через generated `build_openapi_paths()`.

### Если меняется docs-only процесс или policy

- минимум ручная проверка ссылок и консистентности терминов;
- запуск `make docs-check`;
- при изменении нормативных требований проверить, не расходятся ли они с тестовой и архитектурной политикой.

## Quality gates

Перед merge изменение должно:

1. пройти релевантные автоматические тесты;
2. не нарушить CLI contract;
3. не нарушить architecture rules;
4. не нарушить generated/manual boundary policy;
5. не оставить несинхронизированные нормативные документы.

## Verification checklist

Для изменений, затрагивающих `REMOVE` в drift/generation pipeline, перед merge обязательны:

- `remove-only` сценарий: `apidev diff` и `apidev gen --check` возвращают `drift` при наличии только `REMOVE` изменений;
- `remove-conflict` сценарий: apply-режим возвращает `error` со стандартизированным diagnostic code (`remove-conflict` или `remove-boundary-violation`);
- regression-покрытие remove-roundtrip: после успешного `gen` повторный `gen --check` возвращает `no-drift`.

Для изменений, затрагивающих integration contract generated/manual, перед merge обязательны:

- endpoint wiring: operation metadata корректно подключается в runtime router registration;
- auth wiring: для операций с разным `auth` применяется ожидаемая manual dependency policy;
- error wiring: доменные исключения маппятся в контрактные HTTP-ошибки через manual mapper;
- OpenAPI wiring: generated `build_openapi_paths()` детерминированно интегрируется в runtime OpenAPI schema.

## Связь с OpenSpec

- Поведенческие изменения и новые capabilities должны быть отражены в OpenSpec change context.
- Если change вводит новый нормативный сценарий тестирования, он должен отразиться и в этом документе, если правило становится repository-wide.
- `openspec/project.md` остается кратким operational summary и не должен подменять полный testing policy.

## Regression policy

Если найден баг в validate/diff/gen pipeline, по возможности добавляется regression test на минимальном уровне, который стабильно воспроизводит дефект:

- unit, если дефект локальный;
- contract, если нарушен инвариант;
- integration, если поломка видна только в сквозном сценарии.

Документ `docs/process/prompt-improvement-regression-cases.md` является специализированным reference для prompt-related regressions и не подменяет общую тестовую стратегию проекта.

## Связанные документы

- `docs/reference/cli-contract.md`
- `docs/architecture/architecture-rules.md`
- `docs/architecture/validation-blueprint.md`
- `CONTRIBUTING.md`
