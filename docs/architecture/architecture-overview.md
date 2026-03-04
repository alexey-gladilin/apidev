# Архитектурный Обзор APIDev

Статус: `Authoritative`

Этот документ фиксирует текущее архитектурное устройство APIDev и ближайшее направление эволюции. Нормативные правила детализируются в `architecture-rules.md`; этот файл является архитектурным baseline и входной точкой в as-is картину системы.

## Область действия

- `src/apidev/*`
- `tests/unit/architecture/*`
- `tests/contract/architecture/*`
- связанные архитектурные документы из `docs/architecture/*`

## Текущее состояние

APIDev — CLI-инструмент с прагматичной layered/onion архитектурой, где presentation, orchestration, domain core и infrastructure adapters разделены по ответственности.

```mermaid
flowchart TD
    CLI["CLI\nsrc/apidev/cli.py + src/apidev/commands/*"] --> APP["Application\nsrc/apidev/application/*"]
    APP --> CORE["Domain Core\nsrc/apidev/core/*"]
    APP --> INFRA["Infrastructure Adapters\nsrc/apidev/infrastructure/*"]
    INFRA --> FS["Project Files\n.apidev/* + generated files"]
```

### Основные свойства текущего baseline

- `commands/*` обслуживает CLI-вход, UX и composition root.
- `application/*` координирует use cases и pipeline.
- `core/*` содержит доменные модели, правила и порты.
- `infrastructure/*` владеет filesystem, YAML, TOML, Jinja2 и concrete adapters.
- generated/scaffold output ограничен write-boundary внутри `project_dir` с единым path-boundary policy.

## Ключевые потоки

### `init`

`apidev init` создает базовую рабочую структуру проекта и стартовые артефакты, не затрагивая уже существующие generated/manual зоны без явного действия пользователя.

### `validate`

```mermaid
sequenceDiagram
    participant U as User
    participant CMD as commands/validate_cmd
    participant SVC as application/ValidateService
    participant LD as infrastructure/YamlContractLoader
    participant RULE as core/rules/operation_id

    U->>CMD: apidev validate
    CMD->>SVC: run(project_dir)
    SVC->>LD: load(project_dir)
    LD-->>SVC: operations
    SVC->>RULE: ensure_unique_operation_ids(operations)
    SVC-->>CMD: ValidationResult
    CMD-->>U: diagnostics + exit code
```

### `diff`

```mermaid
sequenceDiagram
    participant U as User
    participant CMD as commands/diff_cmd
    participant SVC as application/DiffService
    participant CFG as infrastructure/TomlConfigLoader
    participant LD as infrastructure/YamlContractLoader
    participant RND as infrastructure/JinjaTemplateRenderer
    participant FS as infrastructure/LocalFileSystem

    U->>CMD: apidev diff
    CMD->>SVC: run(project_dir)
    SVC->>CFG: load(project_dir)
    SVC->>LD: load(project_dir)
    SVC->>RND: render templates
    SVC->>FS: compare with existing files
    SVC-->>CMD: GenerationPlan(changes)
    CMD-->>U: file-level diff preview
```

### `gen`

```mermaid
sequenceDiagram
    participant U as User
    participant CMD as commands/generate_cmd
    participant GENSVC as application/GenerateService
    participant DIFF as application/DiffService
    participant WR as infrastructure/SafeWriter

    U->>CMD: apidev gen [--check]
    CMD->>GENSVC: run(project_dir, check)
    GENSVC->>DIFF: run(project_dir)
    DIFF-->>GENSVC: plan(changes)

    alt check=true
        GENSVC-->>CMD: drift_detected=true|false
    else check=false
        GENSVC->>WR: write only ADD/UPDATE changes
        WR-->>GENSVC: writes inside project_dir boundary only
    end

    CMD-->>U: applied changes / drift status
```

## Направление зависимостей

```text
commands -> application -> core
application -> core.ports
infrastructure -> core.ports/core.models
commands -> infrastructure (composition root only)
```

Запрещенные направления раскрываются в `architecture-rules.md`.

## Ближайшее направление эволюции

### Ближайший target state

- сохранить layered/onion baseline;
- усилить boundary между domain core и parsing/adapters;
- удержать `application/*` в роли thin orchestration layer;
- развивать domain models в сторону richer semantics там, где действительно есть инварианты.

### Важная оговорка

Selective DDD для APIDev — это целевое архитектурное направление, а не утверждение, что весь текущий `core/*` уже является rich domain model layer. Часть моделей пока остается lightweight data carriers, и это учитывается в архитектурной документации.

## Связанные документы

- `docs/architecture/README.md`
- `docs/architecture/architecture-rules.md`
- `docs/architecture/generated-integration.md`
- `docs/architecture/validation-blueprint.md`
- `docs/architecture/patterns-and-naming.md`
- `docs/process/testing-strategy.md`
