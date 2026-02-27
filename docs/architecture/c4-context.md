# C4 Level 1: Системный Контекст

## Назначение

Показать границы APIDev, роли пользователей и внешние системы, с которыми инструмент взаимодействует.

## Диаграмма

```mermaid
flowchart LR
    Architect["API Architect / Analyst"]
    Engineer["Backend Engineer"]
    Repo["Target Project Repository"]
    Git["Git / CI"]
    DBSpec["DBSpec (optional, read-only metadata source)"]

    APIDev["APIDev CLI\nContract-driven API scaffolding"]

    Architect -->|"Описывает контракты\n.apidev/contracts/*.yaml"| APIDev
    Engineer -->|"init / validate / diff / gen"| APIDev

    APIDev -->|"Читает/пишет .apidev/*\nи generated код"| Repo
    Repo -->|"Коммит артефактов\n(contracts/templates/generated)"| Git
    APIDev -. optional read-only hints .-> DBSpec
```

## Ключевые выводы

- APIDev является локальным CLI-инструментом оркестрации генерации.
- Основные артефакты живут в репозитории целевого проекта.
- Интеграция с DBSpec опциональная и read-only.
- Каноническая команда генерации в документации — `apidev gen`.
