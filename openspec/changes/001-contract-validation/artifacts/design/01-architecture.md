# Архитектура: Contract Validation Hardening

## Baseline и целевое изменение
Текущий validate-пайплайн использует строковые ошибки и ограниченный набор проверок.
Целевое состояние этапа A: формальный schema + semantic pipeline со структурированной диагностикой и dual output (human/json).

## C4 Level 1: System Context
```mermaid
flowchart LR
    U["Developer / CI"] --> CLI["apidev CLI"]
    CLI --> FS["Project filesystem (.apidev/contracts, config)"]
    CLI --> OUT["STDOUT/STDERR"]
```

## C4 Level 2: Container
```mermaid
flowchart LR
    subgraph APIDEV["apidev"]
      CMD["commands/validate_cmd.py"]
      APP["application/ValidateService"]
      CORE["core validation rules"]
      DTO["diagnostics DTO (structured)"]
      INFRA["infrastructure loaders"]
      PRES["diagnostics presenter (human/json)"]
    end

    CMD --> APP
    APP --> INFRA
    APP --> CORE
    CORE --> DTO
    CMD --> PRES
    PRES --> OUT["stdout"]
```

## C4 Level 3: Component (Validate Flow)
```mermaid
flowchart TD
    A["CLI args (--json, --project-dir)"] --> B["Load config + resolve paths"]
    B --> C["Load YAML contracts"]
    C --> D["Schema validation"]
    D --> E["Semantic validation"]
    E --> F["Collect diagnostics (code,severity,message,location,rule)"]
    F --> G["Render output (human/json)"]
    G --> H["Exit code mapping"]
```

## Архитектурные инварианты
- `commands` остаются thin-адаптером CLI без business-правил.
- `application/core` владеют validation logic и формированием diagnostics.
- Infrastructure отвечает за чтение источников, не за policy.
- Оба формата вывода строятся из одного diagnostics контракта.
