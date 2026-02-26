# APIDev Roadmap

Снимок состояния: 26 февраля 2026.

## 1. Что уже реализовано

- CLI как installable binary: `apidev` entrypoint в `pyproject.toml`.
- Команды MVP:
- `apidev init` (инициализация `.apidev` + стартовый контракт).
- `apidev validate` (загрузка контрактов + проверка уникальности `operation_id`).
- `apidev diff` (план изменений без записи файлов).
- `apidev gen` + alias `apidev generate`.
- Базовый pipeline: `load -> validate -> plan -> render -> write/check`.
- Детерминированная генерация базовых артефактов:
- `operation_map.py`.
- `routers/<operation_id>.py` (скелет endpoint-файлов).
- Safety policy записи:
- запись только внутри `generator.generated_dir`;
- защита от записи в root generated-папки и за ее пределами.
- Режим проверки дрейфа: `apidev gen --check` (non-zero при расхождении).
- Архитектурные guardrail-тесты (слои, зависимости, write-boundary, single source paths).
- Тестовый каркас: unit + contract + integration, все тесты проходят.

## 2. Что частично реализовано или еще не реализовано

- Глубокая валидация контрактов:
- сейчас фактически проверяется только уникальность `operation_id`;
- нет полноценной валидации структуры request/query/response/errors на уровне схемы.
- Генерация transport-слоя:
- шаблон `generated_schema.py.j2` есть, но в текущем pipeline не используется;
- нет генерации полноценных Pydantic-моделей и runtime-роутеров FastAPI.
- Diff-модель:
- сейчас есть `ADD/UPDATE/SAME`, но не реализован полноценный `REMOVE` для удаленных контрактов.
- Совместимость/эволюция контрактов:
- `core/rules/compatibility.py` пока placeholder;
- нет `--fail-on-breaking` и правил semver-совместимости.
- DX и observability CLI:
- нет кодов/категорий диагностики, привязки ошибок к файлам/строкам;
- нет machine-readable вывода (`--json`) для CI-аналитики.
- Интеграции и расширяемость:
- нет интеграции с `dbspec`;
- нет plugin-модели шаблонов/расширений.
- Release automation:
- packaging есть, но pipeline релизной автоматизации (build/publish/changelog gates) не зафиксирован в репозитории как обязательный процесс.

## 3. Где мы сейчас

Текущая стадия: **MVP Foundation / Architecture Baseline Complete**.

Проект уже пригоден как внутренний инструмент для:

- инициализации структуры;
- проверки базовых контрактов;
- предпросмотра изменений;
- безопасной генерации скелета.

Проект пока не готов как production-grade API generator полного цикла (transport models, strict validation, compatibility governance).

## 4. Дорожная карта (предложение по этапам)

## Этап A — Contract Validation Hardening

Цель: превратить `validate` в реальный quality gate.

- Добавить строгую схему контракта и семантические проверки.
- Ввести диагностические коды и file-scoped ошибки.
- Добавить `--json` формат вывода.
- DoD: `validate` блокирует невалидные контракты с точными причинами.

## Этап B — Transport Generation MVP+

Цель: генерировать применимый transport-слой, а не только скелет.

- Подключить генерацию схем (request/response/error models).
- Расширить генерацию роутеров до минимально рабочей FastAPI-формы.
- Зафиксировать стабильный шаблон operation registry + handler bridge контракт.
- DoD: из набора контрактов поднимается минимальный runnable API transport.

## Этап C — Diff/Generate Safety & Drift Governance

Цель: повысить предсказуемость изменений и CI-контроль.

- Добавить `REMOVE` в generation plan.
- Добавить dry-run/check отчеты с итоговой сводкой по типам изменений.
- Добавить режимы `--fail-on-breaking` (после внедрения compatibility rules).
- DoD: CI видит полный спектр drift и breaking-изменений до merge.

## Этап D — Contract Evolution & Integrations

Цель: управляемая эволюция контрактов и экосистемная интеграция.

- Реализовать compatibility rules (breaking/non-breaking classifier).
- Опциональная интеграция с `dbspec` для type hints/nullability/reference hints.
- Политика депрекаций для CLI и контрактов.
- DoD: есть формальные правила миграции контрактов и интеграционный контур.

## Этап E — Productization

Цель: стабильный командный инструмент с прозрачным релизным циклом.

- Release checklist и automation (build/test/version/publish).
- Документация “from zero to first generated endpoint”.
- Расширение e2e/contract тестов по реальным кейсам доменов.
- DoD: повторяемый релизный процесс и предсказуемое внедрение в новые проекты.

## 5. Целевые функциональные возможности (Product Goal)

- Contract-first описание API по endpoint-файлам (YAML) с четкой доменной декомпозицией.
- Строгая валидация контрактов как gate перед генерацией.
- Полный deterministic generation transport-слоя (routes/schemas/error envelopes/operation map).
- Безопасная перегенерация без риска затереть manual-код.
- Проверка drift и breaking changes в CI.
- Поддержка кастомных шаблонов проекта без fork генератора.
- Инкрементальное внедрение в существующие сервисы (модуль за модулем).
- Прозрачная интеграция с lower-level tools (`dbspec`) без жесткой связности.

## 6. Предлагаемые KPI готовности

- `validate` на типовом проекте: < 2 сек для 100 контрактов.
- `gen --check` в CI: стабильный детерминированный результат без ложных срабатываний.
- Доля ручных правок в generated-зоне: 0 (любой drift фиксируется в CI).
- Время от нового контракта до runnable endpoint skeleton: < 10 минут.

