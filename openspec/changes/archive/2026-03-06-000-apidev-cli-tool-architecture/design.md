## Context
`apidev` должен быть распространяемым CLI-бинарником, который исполняется в контексте другого проекта и генерирует transport/API слои по контрактам из `.apidev/contracts`.
Архитектура должна позволять безопасную перегенерацию, прогнозируемый diff и расширяемость команд.

## Goals / Non-Goals
- Goals:
  - выделить четкие слои ответственности внутри CLI-инструмента;
  - обеспечить детерминированный pipeline `load -> validate -> plan -> render -> write`;
  - стандартизировать интерфейсы файловой системы и шаблонизации для тестируемости;
  - определить зависимости и entrypoint бинарника.
- Non-Goals:
  - реализация полнофункционального policy-engine;
  - multi-language генерация;
  - tight coupling на конкретную ORM/DB runtime технологию.

## Decisions
- Decision: использовать слой `commands` как thin adapter для CLI парсинга и UX.
- Decision: бизнес-логика pipeline живет в `application` сервисах.
- Decision: чистые доменные модели контрактов/операций живут в `core` без зависимости от CLI фреймворка.
- Decision: работа с файловой системой, YAML и Jinja идет через `infrastructure` адаптеры.
- Decision: все операции записи в target-проект ограничены policy-областью generated директорий.

## Source Layout (CLI Tool)

```text
.
├── pyproject.toml
├── src/
│   └── apidev/
│       ├── __init__.py
│       ├── cli.py
│       ├── commands/
│       │   ├── __init__.py
│       │   ├── init_cmd.py
│       │   ├── validate_cmd.py
│       │   ├── diff_cmd.py
│       │   └── generate_cmd.py
│       ├── application/
│       │   ├── __init__.py
│       │   ├── services/
│       │   │   ├── init_service.py
│       │   │   ├── validate_service.py
│       │   │   ├── diff_service.py
│       │   │   └── generate_service.py
│       │   └── dto/
│       │       ├── diagnostics.py
│       │       └── generation_plan.py
│       ├── core/
│       │   ├── __init__.py
│       │   ├── models/
│       │   │   ├── contract.py
│       │   │   ├── config.py
│       │   │   └── operation.py
│       │   ├── rules/
│       │   │   ├── operation_id.py
│       │   │   └── compatibility.py
│       │   └── ports/
│       │       ├── filesystem.py
│       │       ├── template_engine.py
│       │       └── contract_loader.py
│       ├── infrastructure/
│       │   ├── __init__.py
│       │   ├── filesystem/
│       │   │   └── local_fs.py
│       │   ├── contracts/
│       │   │   └── yaml_loader.py
│       │   ├── templates/
│       │   │   └── jinja_renderer.py
│       │   └── output/
│       │       └── writer.py
│       └── templates/
│           ├── generated_router.py.j2
│           ├── generated_schema.py.j2
│           └── generated_operation_map.py.j2
└── tests/
    ├── unit/
    │   ├── test_operation_id.py
    │   └── test_validate_service.py
    └── integration/
        └── test_generate_roundtrip.py
```

## Dependency Baseline
Runtime/CLI:
- `typer`
- `rich`
- `pydantic`
- `pydantic-settings`
- `pyyaml`
- `jinja2`
- `tomli-w` (для записи TOML при init)

Developer tooling:
- `pytest`
- `pytest-asyncio`
- `ruff`
- `mypy`

Packaging:
- `build`
- `twine` (release pipeline)

## Command Pipeline Contract
- `apidev init`: создает `.apidev/config.toml`, `.apidev/contracts`, `.apidev/templates` (если отсутствуют).
- `apidev validate`: загружает контракты, валидирует schema/uniqueness, выводит diagnostics.
- `apidev diff`: формирует generation plan и показывает file-level изменения без записи.
- `apidev gen`: применяет plan и записывает только разрешенные generated файлы.

## Write Safety Policy
- По умолчанию запись разрешена только в `generator.generated_dir` из `.apidev/config.toml`.
- Попытки записи за пределы policy path считаются ошибкой конфигурации.
- В режиме `--check` команда завершает процесс с non-zero кодом при обнаружении дрейфа.

## Risks / Trade-offs
- Риск: добавление новых команд приведет к дублированию pipeline логики.
  - Митигация: вынос общей логики в `application/services`.
- Риск: тесная связь с локальной FS затруднит тестирование.
  - Митигация: порты `FileSystemPort` и адаптеры для in-memory тестов.
- Риск: слишком ранняя сложность архитектуры.
  - Митигация: минимальный MVP surface и простые dataclass-модели.

## Migration Plan
1. Создать CLI skeleton с entrypoint `apidev`.
2. Реализовать минимальные команды `init`, `validate`, `diff`, `gen` как вертикальный срез.
3. Добавить unit/integration тесты для operation_id, валидации и генерации.
4. Добавить release pipeline для сборки wheel/sdist.

## Open Questions
- Нужна ли plugin-система шаблонов в MVP или достаточно локальной `.apidev/templates`?
- Нужно ли поддерживать JSON contracts в MVP кроме YAML?
