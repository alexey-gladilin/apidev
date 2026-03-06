# Поведение: Integration Improvements

## 1. `scaffold_dir` и независимые output roots
- `generated_dir` и `scaffold_dir` рассматриваются как два независимых логических контура вывода.
- Независимость не ослабляет безопасность: оба контура проходят единый контроль path-boundary.
- Конфликт путей (пересечение, выход за root, неоднозначная нормализация) приводит к fail-fast диагностике.

### 1.1 Матрица path-конфликтов (`generated_dir` vs `scaffold_dir`)
| Сценарий | Статус | Поведение |
|---|---|---|
| Оба пути внутри `project_dir`, не пересекаются | Допустимо | Генерация продолжается |
| `generated_dir == scaffold_dir` | Недопустимо | Fail-fast validation error |
| `scaffold_dir` вложен в `generated_dir` | Недопустимо | Fail-fast validation error |
| `generated_dir` вложен в `scaffold_dir` | Недопустимо | Fail-fast validation error |
| Любой путь выходит за `project_dir` (включая `..`/symlink escape) | Недопустимо | Fail-fast validation error |
| Нормализация пути неоднозначна и не может быть безопасно разрешена | Недопустимо | Fail-fast validation error |

### 1.2 Минимальный diagnostics contract для fail-fast
- Каждая fail-fast диагностика включает поля: `code`, `message`, `context`.
- `context` содержит только релевантные ключи сценария:
  - path/boundary: `generated_dir`, `scaffold_dir`, `project_dir`;
  - operation metadata: `operation_id`, `field`;
  - type/validation: `field`, `expected_type`, `actual_type`.
- Формат diagnostics должен быть стабильным между повторными запусками при одинаковом входе.
- Canonical serialization:
  - `code` — машинно-стабильный identifier;
  - `message` — человекочитаемое описание;
  - ключи `context` сериализуются в лексикографическом порядке;
  - отсутствующие поля не выводятся;
  - при одинаковом входе diagnostics envelope должен быть байтово-идентичным.

### 1.3 Нормативный каталог fail-fast codes
- `validation.PATH_BOUNDARY_VIOLATION`
- `validation.OUTPUT_CONTOUR_CONFLICT`
- `validation.INVALID_SCAFFOLD_WRITE_POLICY`
- `validation.MANUAL_TAGS_FORBIDDEN`
- `validation.RELEASE_STATE_INVALID_KEY`
- `validation.RELEASE_STATE_TYPE_MISMATCH`
- `config.INIT_PROFILE_INVALID_ENUM`
- `config.INIT_MODE_CONFLICT`

## 2. `scaffold_write_policy`
- Поддерживаются три режима:
- `create-missing`: записывать только отсутствующие scaffold-файлы.
- `skip-existing`: не изменять существующие scaffold-файлы и выдавать детерминированную диагностику пропуска.
- `fail-on-conflict`: при существующем целевом scaffold-файле завершать с ошибкой.
- Если `generator.scaffold_write_policy` не задан, используется `create-missing` (backward-compatible default).
- Политика применяется только к scaffold-контуру и не изменяет поведение generated artifacts.

## 3. Runtime OpenAPI adapter
- Runtime adapter формирует единый набор route descriptors для runtime-фреймворка.
- Для каждой операции нормализуются: method/path/auth/summary/description/deprecated/errors/extensions и домен операции.
- Swagger tags вычисляются из домена операции и не являются отдельным source of truth.
- Адаптер обязан сохранять детерминированный порядок и стабильную сериализацию метаданных.
- Несогласованные или неполные входные данные обрабатываются предсказуемой диагностикой, без частичного «молчаливого» успеха.
- Реализация должна соответствовать reference-контракту из `artifacts/design/05-integration-reference.md`.
- Добавление endpoint в `operation_map` должно автоматически подключать маршрут; вручную добавляются только handler и mapping.
- Если metadata операции содержит ручной `tags`, применяется fail-fast validation error.

## 4. `errors[].example` short-form
- Поддерживается краткая форма `errors[].example` как эквивалент вложенной формы примера.
- Канонизация выполняется до этапа генерации runtime/OpenAPI проекций.
- При одновременном наличии short-form и nested-form:
  - если значения эквивалентны, запись валидна и приводится к канонической nested-модели;
  - если значения конфликтуют, применяется fail-fast validation error с диагностикой.

## 5. `init` integration profiles
- `apidev init` получает профильный слой для integration-сценариев: runtime, integration mode, integration dir.
- Допустимые значения:
  - `--runtime`: `fastapi` | `none`;
  - `--integration-mode`: `off` | `scaffold` | `full`.
- Профиль определяет ожидаемый набор integration-артефактов и их размещение.
- Канонический синтаксис в документации и примерах: `--flag value` (форма `--flag=value` допустима, но не канонична).
- Правила precedence:
  - `--repair` и `--force` взаимоисключающие;
  - profile-флаги управляют только integration-артефактами и не отменяют базовую семантику `create|repair|force`;
  - одинаковые входы и одинаковые флаги дают одинаковый результат.
- Повторный запуск с тем же профилем не должен менять уже согласованное состояние (идемпотентность).

### 5.1 Precedence matrix (`create|repair|force` x profile)
| Режим | Профиль (`runtime`, `integration-mode`, `integration-dir`) | Ожидаемое поведение |
|---|---|---|
| `create` | Валидный профиль | Создает отсутствующие integration-артефакты по профилю; существующие не перезаписываются вне правил профиля |
| `repair` | Валидный профиль | Восстанавливает отсутствующие/поврежденные integration-артефакты; сохраняет пользовательские изменения вне repair-scope |
| `force` | Валидный профиль | Детерминированно пересоздает integration-артефакты в рамках profile-scope |
| `create|repair|force` | `integration-mode=off` | Integration-артефакты не создаются и не обновляются |
| `create|repair|force` | `integration-mode=scaffold` | Управляются только scaffold integration-артефакты |
| `create|repair|force` | `integration-mode=full` | Управляются generated+scaffold integration-артефакты согласно mode |
| Любой | Невалидный enum в `--runtime` или `--integration-mode` | CLI validation error `config.INIT_PROFILE_INVALID_ENUM` до файловых операций |
| Любой | `--repair` и `--force` одновременно | CLI validation error до запуска pipeline |

### 5.2 File-scope matrix для profile-managed artifacts
| `integration-mode` | `runtime` | Managed artifacts | Forbidden mutations |
|---|---|---|---|
| `off` | `fastapi`/`none` | integration-артефакты не создаются и не обновляются | любые записи в integration scaffold/runtime зону |
| `scaffold` | `fastapi` | `<scaffold_dir>/handler_registry.py`, `<scaffold_dir>/router_factory.py`, `<scaffold_dir>/auth_registry.py`, `<scaffold_dir>/error_mapper.py` | изменения generated transport (`operation_map.py`, `openapi_docs.py`, `<domain>/**`) |
| `scaffold` | `none` | `<scaffold_dir>/handler_registry.py`, `<scaffold_dir>/error_mapper.py` | генерация runtime-specific scaffold (`router_factory.py`, `auth_registry.py`) |
| `full` | `fastapi` | scaffold из режима `scaffold` + generated integration (`<generated_dir>/operation_map.py`, `<generated_dir>/openapi_docs.py`, `<generated_dir>/<domain>/**`) | изменения вне profile-scope |
| `full` | `none` | нет | validation error `config.INIT_MODE_CONFLICT` (комбинация запрещена: full требует runtime wiring) |

### 5.3 Политика для `runtime=none`
- `runtime=none` означает запрет runtime-specific wiring артефактов.
- `integration-mode=full` в сочетании с `runtime=none` считается невалидной комбинацией и завершается fail-fast validation error (`config.INIT_MODE_CONFLICT`) до файловых операций.
- Невалидные enum-значения (`--runtime`/`--integration-mode`) завершаются fail-fast validation error (`config.INIT_PROFILE_INVALID_ENUM`) до файловых операций.

## 6. Strict validation release-state
- `release_number` должен соответствовать ожидаемому типу.
- Legacy ключи (например, `current_release`) считаются невалидными в рамках этого change.
- При нарушении формата или типа `apidev` завершает выполнение с явной ошибкой валидации.
- Автоматическая миграция release-state не выполняется.

## 7. Переключатель OpenAPI extensions
- Добавляется `openapi.include_extensions` как явный gate для `x-apidev-*`.
- Значение по умолчанию сохраняет текущее поведение.
- При отключении gate удаляются только extension-поля; все базовые OpenAPI поля и runtime routing остаются неизменными.

## 8. Детерминизм и безопасность
- Для одинаковых входов (`config + contracts`) результат генерации и диагностики идентичен.
- Любое нарушение boundary/policy/compatibility приводит к явной ошибке, а не к неявной деградации.
