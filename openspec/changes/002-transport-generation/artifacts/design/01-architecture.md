# Архитектура: Transport Generation MVP+

## Baseline и целевое изменение
Baseline generation-пайплайн формирует operation map и router skeleton-файлы.
Целевое состояние этапа B: расширенный deterministic transport generation с model artifacts, runnable wiring и стабильным bridge/registry contract.

## C4 Level 1: System Context
```mermaid
flowchart LR
    U["Developer / CI"] --> CLI["apidev CLI"]
    CLI --> CONTRACTS["Contract files (.apidev/contracts)"]
    CLI --> GEN["Generated transport zone"]
    CLI --> OUT["STDOUT / Drift signals"]
    MANUAL["Manual application handlers"] --> GEN
```

## C4 Level 2: Container
```mermaid
flowchart LR
    subgraph APIDEV["apidev"]
      CMD["commands/generate_cmd.py"]
      APP_DIFF["application/DiffService"]
      APP_GEN["application/GenerateService"]
      CORE["core contract + operation rules"]
      TMPL["jinja templates"]
      WRITER["SafeWriter"]
    end

    CMD --> APP_GEN
    APP_GEN --> APP_DIFF
    APP_DIFF --> CORE
    APP_DIFF --> TMPL
    APP_GEN --> WRITER
    WRITER --> OUT_FS["generated root"]
    OUT_FS --> BRIDGE["manual handler bridge"]
```

## C4 Level 3: Component (Transport Generation Flow)
```mermaid
flowchart TD
    A["Load config + resolve paths"] --> B["Load contracts"]
    B --> C["Validate operation_id uniqueness"]
    C --> D["Build generation plan"]
    D --> E["Render operation registry"]
    D --> F["Render router artifacts"]
    D --> G["Render request/response/error model artifacts"]
    E --> H["Apply ADD/UPDATE via SafeWriter"]
    F --> H
    G --> H
    H --> I["Drift check / applied changes report"]
```

## Архитектурные инварианты
- CLI остается thin orchestration-слоем без бизнес-логики.
- Planning/rendering выполняется в application/core, а не в infrastructure writer.
- Запись остается ограниченной generated root.
- Generated transport слой не владеет domain/service implementation и взаимодействует с manual кодом только через bridge contract.
