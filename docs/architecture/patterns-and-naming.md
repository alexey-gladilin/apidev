# Паттерны И Нейминг В Кодовой Базе

Статус: `Reference`

Этот документ описывает фактические паттерны и naming tendencies в кодовой базе APIDev. Нормативные правила находятся в `architecture-rules.md`; здесь собраны rationale, примеры и полезные наблюдения.

## Что реально использует APIDev

### Доминирующие паттерны

- layered/onion architecture с направлением зависимостей `commands -> application -> core`;
- ports and adapters через `core/ports/*` и `infrastructure/*`;
- composition root в command layer;
- deterministic pipeline `load -> validate -> plan -> render -> write/check`;
- архитектурные ограничения, поддержанные тестами.

### Де-факто нейминг

- пакеты отражают слой ответственности:
  - `commands`
  - `application`
  - `core`
  - `infrastructure`
- orchestration классы обычно используют суффикс `*Service`;
- абстракции используют суффикс `*Port`;
- concrete adapters именуются по роли, а не через универсальное `*Adapter`;
- command modules следуют шаблону `<verb>_cmd.py`.

## Обоснование

### Почему слой `commands` должен оставаться тонким

Тонкие command handlers:

- упрощают CLI-слой;
- делают composition root явным;
- уменьшают риск дублирования orchestration logic;
- облегчают тестирование сервисов отдельно от Typer/CLI wiring.

### Почему parsing и external formats остаются на границе

YAML, TOML, filesystem и template rendering являются внешними concern-ами. Их удержание в `infrastructure/*` снижает связность `core/*` и облегчает архитектурную валидацию.

### Почему naming важен

Стабильный naming помогает:

- быстрее читать layered codebase;
- однозначно понимать роль модуля;
- проектировать test cases по ответственности;
- автоматизировать review и архитектурные проверки.

## Рекомендуемая naming taxonomy

### Типы

- `*Service` — orchestration/use case
- `*Port` — абстракция
- `*Loader`, `*Renderer`, `*Writer`, `*FileSystem` — concrete infra roles
- `*Result`, `*Plan`, `*Config`, `*Paths`, `*Issue`, `*Error` — DTO и state types

### Модули

- `snake_case` для всех Python modules;
- verb-led имена для entrypoints и pipeline-oriented модулей;
- noun-led имена для устойчивых domain concepts и diagnostics;
- избегать `helpers` и `misc` для значимой логики.

### Функции

- `load_*` — загрузка ресурсов;
- `parse_*` — преобразование raw input;
- `resolve_*` — derived paths и runtime decisions;
- `validate_*` — rule checks;
- `build_*` — deterministic assembly;
- `render_*` — text/template generation;
- `write_*` — persistence;
- `ensure_*` — assertions и invariant checks.

## Текущие пробелы

- selective DDD в документации выражен сильнее, чем пока реализован в коде;
- `core/models/config.py` использует Pydantic как практический компромисс, хотя target architecture стремится держать boundary parsing вне core;
- naming policy уже достаточно стабильна, но исторически была размазана между несколькими документами.

## Примеры

- `src/apidev/commands/generate_cmd.py`
- `src/apidev/application/services/generate_service.py`
- `src/apidev/core/rules/operation_id.py`
- `src/apidev/infrastructure/contracts/yaml_loader.py`
- `src/apidev/infrastructure/output/writer.py`

## Связанные документы

- `docs/architecture/architecture-overview.md`
- `docs/architecture/architecture-rules.md`
- `docs/architecture/team-conventions.md`
