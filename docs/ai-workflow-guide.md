# AI Workflow Guide

Практический справочник по текущему AI-процессу в репозитории: какие команды запускать, какие агенты участвуют и кто за что отвечает.

## 1. Что является источником правды

- OpenSpec change-контекст: `openspec/changes/<change-id>/`
- Core-файлы change:
  - `proposal.md`
  - `design.md`
  - `tasks.md`
  - `specs/<capability>/spec.md`
- Артефакты процесса:
  - `openspec/changes/<change-id>/artifacts/research/`
  - `openspec/changes/<change-id>/artifacts/design/`
  - `openspec/changes/<change-id>/artifacts/plan/`
- Правило single writer:
  - только orchestrator обновляет runtime-статусы в `tasks.md`.

## 2. End-to-End процесс (OpenSpec)

1. `Research`
2. `Design`
3. `Plan`
4. `Implement`
5. `Archive`

Рекомендуемый путь:

1. `/openspec-proposal <change-id>`
2. `/research-codebase <change-id> "<question>"`
3. `/design-feature <change-id> <feature-name> "<description>"`
4. `/openspec-implement <change-id>` или `/openspec-implement-single <change-id>`
5. `/openspec-archive <change-id>` после деплоя

## 3. Команды: что и когда запускать

### OpenSpec команды


| Команда                      | Когда использовать                   | Что делает                                                  | Выход                                                                           |
| ---------------------------- | ------------------------------------ | ----------------------------------------------------------- | ------------------------------------------------------------------------------- |
| `/openspec-proposal`         | старт новой capability/изменения     | scaffolding change + базовые артефакты Research/Design/Plan | `proposal.md`, `design.md`, `tasks.md`, spec deltas, artifact-контур            |
| `/research-codebase`         | нужен фактологический As-Is анализ   | собирает fact-only исследование кода                        | research-файл в `artifacts/research/` + ссылки в core                           |
| `/design-feature`            | после research для проектирования    | формирует дизайн-пакет и фазовый план без кода              | файлы в `artifacts/design/`, `artifacts/plan/`, sync с `design.md` и `tasks.md` |
| `/openspec-implement`        | основной multi-agent implementation  | оркестрирует subagents и quality gates                      | изменения кода + обновленный статус `tasks.md`                                  |
| `/openspec-implement-single` | когда недоступны subagents/Task tool | выполняет те же gate-этапы в single-agent режиме            | изменения кода + обновленный статус `tasks.md`                                  |
| `/openspec-archive`          | change задеплоен                     | архивирует change и применяет обновления spec               | папка в `openspec/changes/archive/...`                                          |


### DBSpec команды


| Команда                        | Назначение                            | Ключевой результат          |
| ------------------------------ | ------------------------------------- | --------------------------- |
| `/dbspec-report-env-readiness` | проверка готовности окружения DBSpec  | `env_readiness` отчет       |
| `/dbspec-audit-naming`         | аудит нейминга SSOT                   | `naming_consistency` отчет  |
| `/dbspec-report-migrations`    | аудит миграционного состояния         | `migration_health` отчет    |
| `/dbspec-report-ssot-db`       | сверка SSOT и DB                      | `ssot_db_consistency` отчет |
| `/dbspec-report-full`          | полный сводный DBSpec аудит           | `combined_health` отчет     |
| `/dbspec-report-delta`         | сравнение двух последних отчетов типа | `delta_health` отчет        |


Все DBSpec команды используют skill `dbspec-ops-reporter` и пишут отчеты в `.dbspec/reports/` (`.md` + `.json`).

## 4. Агенты и роли


| Агент                  | Роль                                       | Где применяется       | Что возвращает                                                               |
| ---------------------- | ------------------------------------------ | --------------------- | ---------------------------------------------------------------------------- |
| `openspec-implementer` | orchestration implementation pipeline      | `/openspec-implement` | координация этапов, маршрутизация gate-ов, обновление `tasks.md`             |
| `spec-analyst`         | gate готовности спецификации               | перед кодом           | `SPEC READY` или `SPEC REJECTED`                                             |
| `coder`                | реализация по RED-GREEN-REFACTOR           | coding этап           | `HANDOFF TO ORCHESTRATOR`                                                    |
| `tester`               | проверка тестов и challenge coverage       | после coder           | `VERIFIED` или `REJECTION`                                                   |
| `security`             | security review                            | после tester          | `SECURITY VERIFIED` или `REJECTION`                                          |
| `qa`                   | финальный quality/architecture/spec review | после security        | `APPROVED` или `REJECTION`                                                   |
| `codebase-researcher`  | узкий фактологический исследователь        | `/research-codebase`  | `Summary`, `Findings`, `Code references`, `Open questions`, `Fact/Inference` |


### 4.1 `openspec-implementer` (Orchestrator)

Что делает:

- Запускает и координирует pipeline `spec-analyst -> coder -> tester -> security -> qa`.
- Выбирает режим исполнения: `AUTO`, `STRICT`, `BATCH`.
- Маршрутизирует rejections обратно в coding-loop.
- Единственный обновляет runtime-статусы в `tasks.md` (single writer).

Что проверяет:

- `openspec validate <change-id> --strict --no-interactive`.
- Наличие и готовность контекста (`proposal.md`, `design.md`, `tasks.md`, spec deltas, artifacts).
- Pre-flight по conventions и test infrastructure.

Что отдает:

- Текущий прогресс по tasks.
- Финальный summary по change.
- Список blocked/pending задач с причинами.

Ограничения:

- Не делегирует обновление `tasks.md` субагентам.
- Не пропускает обязательные gates.

### 4.2 `spec-analyst`

Что делает:

- Проверяет готовность change к реализации до любого кода.
- Оценивает completeness, clarity, consistency и dependency integrity.

Что проверяет:

- Полноту `proposal.md`, `design.md`, `tasks.md`, spec deltas.
- Отсутствие противоречий с `openspec/specs/*` и `openspec/project.md`.
- Исполнимый порядок задач без скрытых зависимостей.

Что отдает:

- `SPEC READY` или `SPEC REJECTED`.
- Структурированный отчет с file:line findings и required actions.

Ограничения:

- Не пишет код.
- Не обновляет статусы в `tasks.md`.

### 4.3 `coder`

Что делает:

- Реализует назначенный scope задач по TDD (RED-GREEN-REFACTOR).
- Работает по явному scope от orchestrator (task, wave или batch).
- Формирует handoff с перечнем изменений и тестов.

Что проверяет:

- Pre-flight: conventions + test infra.
- Корректность реализации относительно задачи и spec context.

Что отдает:

- `HANDOFF TO ORCHESTRATOR`:
  - task id и description
  - измененные файлы
  - тестовые файлы
  - команды и краткое резюме.

Ограничения:

- Не вызывает других агентов напрямую.
- Не обновляет `tasks.md`.
- Не расширяет scope вне явно назначенного.

### 4.4 `tester`

Что делает:

- Независимо валидирует реализацию через выполнение тестов.
- Проверяет качество test coverage и пытается "сломать" реализацию.

Что проверяет:

- Корректность handoff.
- Запуск проектных тестов документированными командами.
- Coverage по категориям: happy path, null/undefined, empty input, boundary, error handling.

Создает ли тесты:

- Да. Если покрытие проседает (2+ категории не покрыты), добавляет challenge tests и запускает их.

Что отдает:

- `VERIFIED` или `REJECTION` с evidence и failed output.

Ограничения:

- Не фиксит production-код.
- Не обновляет `tasks.md`.
- Возвращает вердикт только orchestrator-у.

### 4.5 `security`

Что делает:

- Проводит security gate после tester.
- Проверяет риски по валидации, authn/authz, secret handling, dependency/supply-chain и secure defaults.

Что проверяет:

- Безопасность trust boundaries и архитектурных границ.
- Отсутствие утечек секретов.
- Соответствие security требованиям проекта.

Что отдает:

- `SECURITY VERIFIED` или `REJECTION` с severity и actionable findings.

Ограничения:

- Не исправляет код.
- Не обновляет `tasks.md`.
- Не маршрутизирует дальше напрямую, только возвращает verdict orchestrator-у.

### 4.6 `qa`

Что делает:

- Финальный gate перед закрытием задачи.
- Проверяет соответствие OpenSpec, архитектуру, maintainability и code quality.

Что проверяет:

- Соответствие реализованного поведения spec.
- Границы слоев и зависимостей.
- Общую читаемость и поддерживаемость решения.

Что отдает:

- `APPROVED` или `REJECTION` с file:line findings.

Ограничения:

- Не запускает тесты как primary responsibility.
- Не обновляет `tasks.md`.
- Финальный вердикт отправляет orchestrator-у.

### 4.7 `codebase-researcher`

Что делает:

- Выполняет узкие параллельные research-задачи в рамках `/research-codebase`.
- Возвращает только факты по текущему состоянию системы (as-is).

Что проверяет:

- Ключевые тезисы с привязкой к `file:line`.
- Явное разделение фактов и выводов.

Что отдает:

- `Summary`
- `Findings`
- `Code references`
- `Open questions`
- `Fact / Inference`.

Ограничения:

- Не предлагает улучшения.
- Не проектирует to-be.
- Не пишет production-код.


## 5. Gate-модель в Implement

Обязательный порядок:

1. Pre-flight (conventions + test infra)
2. Spec readiness (`spec-analyst`)
3. Coding (`coder`)
4. Tester gate
5. Security gate
6. QA gate
7. Final project quality gates (format/lint/test)

Режимы:

- `AUTO` — wave-based, быстрее по токенам.
- `STRICT` — один task за раз, полный pipeline на каждый task.
- `BATCH` — код по всем pending tasks, затем полный gate-проход в конце.

## 6. Как читать `tasks.md`

Поддерживаемые статусы:

- `[ ]` pending
- `[x]` completed
- `[REJECTED xN]` отклонено N раз
- `[BLOCKED - NEEDS HUMAN REVIEW]` требуется вмешательство человека

Правила:

- В `proposal/design/plan` фазах формируй плановые пункты (`[ ]`) без runtime-статусов.
- Runtime-статусы проставляются только в implement-фазе orchestrator-ом.

## 7. Практика использования (быстрые сценарии)

### Сценарий A: новая фича

1. `/openspec-proposal add-<feature>`
2. `/research-codebase add-<feature> "<вопрос исследования>"`
3. `/design-feature add-<feature> <feature-name> "<контекст>"`
4. `/openspec-implement add-<feature>`
5. После деплоя: `/openspec-archive add-<feature>`

### Сценарий B: среда без subagents

1. Подготовить change через proposal/research/design.
2. Запустить `/openspec-implement-single <change-id>`.
3. Пройти внутренние gate-этапы в том же порядке: Tester -> Security -> QA.

### Сценарий C: операционный аудит DBSpec

1. `/dbspec-report-env-readiness`
2. `/dbspec-report-full`
3. При повторном запуске для тренда: `/dbspec-report-delta`

## 8. Частые ошибки и как избежать

- Ошибка: запуск Implement без approved proposal.  
Решение: сначала validation + подтверждение proposal.
- Ошибка: артефакты вне `openspec/changes/<change-id>/artifacts/`.  
Решение: сохранять Research/Design/Plan только внутри change.
- Ошибка: subagent пытается менять `tasks.md`.  
Решение: соблюдать single writer; статус меняет только orchestrator.
- Ошибка: пропуск Security/QA gate ради скорости.  
Решение: сохранять обязательный порядок gate-ов даже в `AUTO`.

## 9. Минимальный operational checklist перед работой

1. Проверить `openspec/AGENTS.md`.
2. Проверить, что `change-id` существует и валиден: `openspec validate <change-id> --strict --no-interactive`.
3. Убедиться, что структура `artifacts/{research,design,plan}` на месте.
4. Убедиться, что в `tasks.md` есть исполнимые пункты.
5. Выбрать режим implement (`AUTO`/`STRICT`/`BATCH`) по риску.
