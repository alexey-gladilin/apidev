## Контекст
`apidev` уже обеспечивает deterministic generation, но интеграционный слой остается частично ручным: ограничения `scaffold_dir`, отсутствие режима выбора политики scaffold-записи, неполный runtime/OpenAPI adapter.
Текущий change фиксирует архитектурные решения для безопасной и предсказуемой интеграции в существующие runtime-проекты.

## Цели / Не-цели
- Цели:
  - отделить `scaffold_dir` от `generated_dir` без ослабления security boundaries;
  - ввести явную scaffold write policy;
  - формализовать runtime adapter с metadata для OpenAPI/роутинга;
  - поддержать `errors[].example` short-form;
  - добавить profile-флаги для `init`;
  - добавить toggle `openapi.include_extensions`.
  - зафиксировать strict validation release-state формата и типов.
- Не-цели:
  - изменение доменной модели контрактов beyond declared compatibility;
  - изменение бизнес-логики runtime-приложения;
  - миграция release-state и поддержка legacy release-state ключей;
  - реализация production-кода в рамках proposal-фазы.

## Решения
- Вводится двухконтурная output-модель (`generated_dir` + `scaffold_dir`) с единым path-boundary policy.
- Вводится конфиг `generator.scaffold_write_policy` (`create-missing`, `skip-existing`, `fail-on-conflict`) для детерминированного поведения scaffold-артефактов.
- Значение `generator.scaffold_write_policy` по умолчанию — `create-missing`, чтобы без явной опции сохранялось текущее поведение.
- Runtime adapter и OpenAPI projection используют единую нормализованную operation metadata, чтобы избежать дрейфа между runtime routing и documentation.
- Домен endpoint-а определяется из структуры операций; Swagger tags вычисляются из домена автоматически.
- `errors[].example` нормализуется в каноническую error-example модель до этапа генерации.
- При наличии и short-form, и nested-form:
  - совпадающие значения считаются валидными и приводятся к канонической nested-модели;
  - конфликтующие значения приводят к fail-fast validation error.
- Release-state валидируется строго: legacy-ключи и неверные типы считаются ошибкой валидации без миграционного fallback.
- `init` расширяется integration profile-флагами с идемпотентным поведением в режимах `repair/force`:
  - `--runtime`: `fastapi | none`;
  - `--integration-mode`: `off | scaffold | full`;
  - `--integration-dir`: путь внутри `project_dir`, проходящий общий boundary-контроль;
  - `--repair` и `--force` остаются взаимоисключающими; profile-флаги не отменяют это правило.
- `openapi.include_extensions` управляет только `x-apidev-*`, не затрагивая базовые OpenAPI поля.

## Риски / Компромиссы
- Риск: более гибкий `scaffold_dir` может усилить риск неправильной path-конфигурации.
  - Митигация: fail-fast валидация и единый boundary policy.
- Риск: runtime adapter может разойтись с текущими templates.
  - Митигация: snapshot/integration tests на согласованность metadata.
- Риск: ручные `tags` могут расходиться с доменной структурой и давать неоднозначную Swagger-группировку.
  - Митигация: `tags` не являются входным источником истины; при конфликтной metadata применяется fail-fast валидация.
- Риск: более строгая release-state валидация может выявить проблемы в существующих конфигурациях.
  - Митигация: явные diagnostics с указанием ключа и ожидаемого типа.

## Migration Plan
1. Ввести новые конфиг-поля и compatibility of default behavior (без изменения default-поведения для пользователей без новых опций).
2. Добавить runtime/openapi adapter projection и покрыть snapshot-контрактами.
3. Расширить `init` профилями и обновить docs.
4. Зафиксировать regression matrix и strict OpenSpec validation.

Примечание: migration/fallback для legacy release-state форматов в scope не входит; parser остается strict.

## Linked Artifacts
- Research: [artifacts/research/2026-03-03-integration-improvements-baseline.md](./artifacts/research/2026-03-03-integration-improvements-baseline.md)
- Design package index: [artifacts/design/README.md](./artifacts/design/README.md)
- Architecture: [artifacts/design/01-architecture.md](./artifacts/design/01-architecture.md)
- Behavior: [artifacts/design/02-behavior.md](./artifacts/design/02-behavior.md)
- Decisions: [artifacts/design/03-decisions.md](./artifacts/design/03-decisions.md)
- Testing: [artifacts/design/04-testing.md](./artifacts/design/04-testing.md)
- Integration reference: [artifacts/design/05-integration-reference.md](./artifacts/design/05-integration-reference.md)
- Plan package: [artifacts/plan/README.md](./artifacts/plan/README.md)
- Spec delta: [specs/cli-tool-architecture/spec.md](./specs/cli-tool-architecture/spec.md)

## Готовность к Implement
После approval этот change-пакет является входом для отдельной implement-команды.

## Синхронизация архитектурных правил
- Для `012-integration` применяется boundary-модель: `generated_dir` и `scaffold_dir` как независимые output-контуры внутри `project_dir`.
- Repository-wide архитектурные документы синхронизируются с этим правилом:
  - `docs/architecture/architecture-overview.md`
  - `docs/architecture/architecture-rules.md`
  - `docs/architecture/validation-blueprint.md`
  - `docs/architecture/generated-integration.md`.
