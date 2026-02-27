# C4 Level 3: Компонентная Модель APIDev

## Назначение

Показать компоненты внутри APIDev и их зависимостные границы.

## Общая диаграмма компонентов

```mermaid
flowchart LR
    subgraph Presentation["Presentation Layer"]
        CLI["CLI Commands\nsrc/apidev/commands/*"]
    end

    subgraph AppCore["Application Core"]
        INIT["InitService"]
        VAL["ValidateService"]
        DIFF["DiffService"]
        GEN["GenerateService"]
    end

    subgraph Domain["Domain Core"]
        MODELS["core/models/*\n(rich models, value objects)"]
        RULES["core/rules/*"]
        PORTS["core/ports/*\n(ContractLoaderPort,\nTemplateEnginePort,\nConfigLoaderPort,\nWriterPort)"]
        CFG["ApidevConfig models"]
    end

    subgraph Infra["Infrastructure Adapters"]
        YAML["YamlContractLoader\n+ boundary parsing"]
        J2["JinjaTemplateRenderer"]
        LFS["LocalFileSystem"]
        WR["SafeWriter"]
    end

    CLI --> INIT
    CLI --> VAL
    CLI --> DIFF
    CLI --> GEN

    INIT --> PORTS
    VAL --> PORTS
    VAL --> RULES
    DIFF --> PORTS
    DIFF --> RULES
    DIFF --> CFG
    GEN --> DIFF

    INIT --> LFS
    VAL --> YAML
    DIFF --> YAML
    DIFF --> J2
    DIFF --> LFS
    GEN --> WR

    RULES --> MODELS
```

## Критичные инварианты L3

- `application/*` не импортирует concrete adapters из `infrastructure/*`.
- `core/*` не выполняет direct I/O и не зависит от `commands/application/infrastructure`.
- `commands/*` остаются thin adapters без бизнес-правил.
- `SafeWriter` реализует `WriterPort` и обеспечивает write-boundary только внутри generated root.
- Boundary parsing/shape validation остаются в adapters or edge-facing layers; `core/*` работает с доменными понятиями, а не raw payload.
- `core/models/*` может содержать rich models и value objects с поведением, если это поведение относится к инвариантам модели.
