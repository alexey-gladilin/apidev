# 01. Architecture

## System Context (C4 Level 1)
```mermaid
C4Context
    title APIDev - Contract Example Support (L1)
    Person(api_designer, "API Designer", "Определяет YAML-контракты")
    System(apidev, "APIDev CLI", "Валидирует контракты и генерирует transport/OpenAPI артефакты")
    System_Ext(git_repo, "Git Repository", "Хранит contracts/templates/generated артефакты")

    Rel(api_designer, apidev, "Запускает validate/diff/gen", "CLI")
    Rel(apidev, git_repo, "Читает/пишет артефакты", "Filesystem")
```

## Container View (C4 Level 2)
```mermaid
C4Container
    title APIDev Containers - Example Field Flow (L2)
    Person(api_designer, "API Designer")
    Container(cli, "CLI Commands", "Typer", "init/validate/diff/gen orchestration")
    Container(app_services, "Application Services", "Python", "ValidateService/DiffService")
    Container(core_rules, "Core Rules", "Python", "Contract schema + semantic validation")
    Container(templates, "Template Engine", "Jinja2", "Generate router/schema/openapi docs")
    ContainerDb(fs, "Project Filesystem", "YAML/TOML/Python", "contracts/templates/generated")

    Rel(api_designer, cli, "Runs commands")
    Rel(cli, app_services, "Invokes")
    Rel(app_services, core_rules, "Validates contract schema")
    Rel(app_services, templates, "Renders generated artifacts")
    Rel(app_services, fs, "Reads/Writes files")
    Rel(core_rules, fs, "Reads contract data")
    Rel(templates, fs, "Writes generated code")
```

## Component View (C4 Level 3)
```mermaid
C4Component
    title Validate + Generate Components for `example` Field (L3)
    Container_Boundary(apidev_boundary, "APIDev") {
        Component(validate_service, "ValidateService", "application/services/validate_service.py", "Orchestrates schema + semantic checks")
        Component(schema_rules, "contract_schema", "core/rules/contract_schema.py", "Strict schema validator incl. `example`")
        Component(diff_service, "DiffService", "application/services/diff_service.py", "Builds deterministic generation plan")
        Component(openapi_tpl, "generated_openapi_docs.py.j2", "templates", "OpenAPI metadata rendering")
        Component(schema_tpl, "generated_schema.py.j2", "templates", "Transport schema rendering")
    }

    Rel(validate_service, schema_rules, "validate_contract_schema(document)")
    Rel(diff_service, schema_tpl, "render transport models with schema fragment")
    Rel(diff_service, openapi_tpl, "render OpenAPI paths with metadata")
    Rel(schema_rules, diff_service, "validated schema available for generation")
```

## Boundary Rules
- Generated code remains transport-only; business logic не генерируется.
- Unknown-field policy сохраняется strict, кроме явно разрешенного `example`.
- Output remains deterministic for identical contract inputs.
