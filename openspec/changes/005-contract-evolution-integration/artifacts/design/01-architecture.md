# 01. Architecture

## System Context (C4 Level 1)
```mermaid
C4Context
    title APIDev - Contract Evolution & Integrations (L1)
    Person(api_designer, "API Designer", "Определяет и эволюционирует YAML-контракты")
    System(apidev, "APIDev CLI", "Validate/Diff/Gen и governance проверка совместимости")
    System_Ext(git_repo, "Git Repository", "Хранит contracts/templates/generated artifacts")

    Rel(api_designer, apidev, "Запускает validate/diff/gen", "CLI")
    Rel(apidev, git_repo, "Читает/пишет artifacts", "Filesystem")
```

## Container View (C4 Level 2)
```mermaid
C4Container
    title APIDev Containers - Evolution Governance (L2)
    Person(api_designer, "API Designer")
    Container(cli, "CLI Commands", "Typer", "init/validate/diff/gen orchestration")
    Container(app_services, "Application Services", "Python", "ValidateService/DiffService/GenerateService")
    Container(core_rules, "Core Rules", "Python", "Schema/semantic/compatibility classification")
    Container(templates, "Template Engine", "Jinja2", "Generate transport/OpenAPI artifacts")
    ContainerDb(fs, "Project Filesystem", "YAML/TOML/Python", "contracts/config/generated")

    Rel(api_designer, cli, "Runs commands")
    Rel(cli, app_services, "Invokes")
    Rel(app_services, core_rules, "Evaluates compatibility + deprecation lifecycle")
    Rel(app_services, templates, "Renders deterministic output")
    Rel(app_services, fs, "Reads/Writes generated zone")
    Rel(infra_loaders, fs, "Reads contracts/config")
```

## Component View (C4 Level 3)
```mermaid
C4Component
    title Components for Stage D (L3)
    Container_Boundary(apidev_boundary, "APIDev") {
        Component(diff_service, "DiffService", "application/services/diff_service.py", "Builds generation plan and diff preview")
        Component(generate_service, "GenerateService", "application/services/generate_service.py", "Applies plan / check mode")
        Component(compat_rules, "compatibility rules", "core/rules/compatibility.py", "Classifies changes by compatibility")
        Component(deprecation_policy, "deprecation policy", "core/rules/*", "Tracks active/deprecated/removed lifecycle")
        Component(contract_loader, "contract loaders", "infrastructure/contracts", "Loads YAML contract documents")
    }

    Rel(diff_service, compat_rules, "classify(change_set)")
    Rel(generate_service, compat_rules, "enforce mode/check policy")
    Rel(diff_service, deprecation_policy, "evaluate lifecycle transitions")
    Rel(diff_service, contract_loader, "load contract docs")
```

## Boundary Rules
- Compatibility/deprecation решения остаются deterministic и test-backed.
