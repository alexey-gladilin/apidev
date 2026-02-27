# C4 Level 2: Контейнерная Модель

## Назначение

Описать основные контейнеры/подсистемы APIDev и ключевые потоки между ними.

## Диаграмма контейнеров

```mermaid
flowchart TD
    CLI["Container: CLI\nsrc/apidev/cli.py + src/apidev/commands/*"]
    APP["Container: Application Services\nsrc/apidev/application/*"]
    CORE["Container: Domain Core\nsrc/apidev/core/*"]
    INFRA["Container: Infrastructure Adapters\nsrc/apidev/infrastructure/*"]
    FS["Container: Local File Storage\n.apidev/* + generated tree"]

    CLI -->|"Командный сценарий"| APP
    APP -->|"Use-case orchestration"| CORE
    APP -->|"Ports/adapters calls"| INFRA
    INFRA -->|"Read/write files,\nload contracts,\nrender templates"| FS
```

## Контейнеры и ответственность

| Контейнер | Ответственность | Ключевые модули |
|---|---|---|
| CLI | Parse/dispatch команд, UX-output | `src/apidev/cli.py`, `src/apidev/commands/*` |
| Application Services | Thin orchestration pipeline `load/validate/plan/write`; mapping boundary models to domain models | `src/apidev/application/services/*` |
| Domain Core | Selective DDD core: rich models, value objects, rules, ports | `src/apidev/core/models/*`, `src/apidev/core/rules/*`, `src/apidev/core/ports/*` |
| Infrastructure Adapters | YAML/Jinja/FS/writer реализации; boundary parsing and external format adapters | `src/apidev/infrastructure/*` |
| Local File Storage | Хранение контрактов, templates, generated output | `.apidev/*`, target generated dir |

## Главные архитектурные границы

- `core` не зависит от `application`, `commands`, `infrastructure`.
- `application` опирается на порты core и не должен знать concrete adapters.
- Все filesystem side-effects локализованы в infrastructure.
- Pydantic и другие schema/boundary validators используются на границе внешних форматов и не подменяют rich domain core.
- В walkthrough и примерах для генерации используется `apidev gen`.
