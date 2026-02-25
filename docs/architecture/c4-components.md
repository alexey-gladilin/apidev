# C4 Level 3: Component View (APIDev Python App)

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
        MODELS["core/models/*"]
        RULES["core/rules/*"]
        PORTS["core/ports/*\n(ContractLoaderPort,\nTemplateEnginePort,\nConfigLoaderPort,\nWriterPort)"]
        CFG["ApidevConfig models"]
    end

    subgraph Infra["Infrastructure Adapters"]
        YAML["YamlContractLoader"]
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
