# Архитектура: Integration Improvements (`012-integration`)

## Контекст
Нужно расширить integration-контур `apidev` без нарушения:
- безопасных границ записи в файловую систему;
- детерминированности генерации и диагностики;
- стабильности существующих сценариев без новых опций.

## Архитектурные цели
- Развязать `scaffold_dir` и `generated_dir` как независимые output-контуры.
- Сделать запись scaffold явной и управляемой политикой.
- Синхронизировать runtime routing и OpenAPI metadata через единый адаптер.
- Ввести конфигурируемость OpenAPI extensions без изменения core-контракта.

## C4 Level 1: System Context
```mermaid
C4Context
title APIDev Integration Improvements (L1)
Person(dev, "Developer / CI", "Запускает init/gen/diff, управляет конфигом и контрактами")
System(apidev, "apidev CLI", "Contract-driven генерация и integration scaffolding")
System_Ext(fs, "Project Filesystem", "config, contracts, generated artifacts, scaffold artifacts")
System_Ext(runtime, "Runtime Framework", "Приложение, принимающее маршруты и OpenAPI metadata")

Rel(dev, apidev, "Запускает команды и настраивает профили")
Rel(apidev, fs, "Читает/пишет артефакты в разрешенных границах")
Rel(apidev, runtime, "Поставляет runtime adapter и metadata для add_api_route")
```

## C4 Level 2: Container
```mermaid
C4Container
title APIDev Containers for Integration (L2)
Person(dev, "Developer / CI")
System_Boundary(apidev_boundary, "apidev") {
  Container(cli, "CLI Layer", "Typer", "init/gen/diff entrypoints и runtime flags")
  Container(config, "Config & Validation", "Core Models + Rules", "Нормализация параметров и schema совместимость")
  Container(gen, "Generation Orchestrator", "Application Services", "Детерминированный план генерации")
  Container(scaffold, "Scaffold Planner", "Application Services", "Разрешение scaffold_dir и применение scaffold_write_policy")
  Container(runtime_adapter, "Runtime OpenAPI Adapter", "Generated Runtime Layer", "Единая модель маршрута + OpenAPI metadata")
}
System_Ext(fs, "Filesystem", "project-root bounded read/write")
System_Ext(runtime, "Runtime Framework", "Router API")

Rel(dev, cli, "Вызовы команд")
Rel(cli, config, "Передает флаги/конфиг")
Rel(cli, gen, "Инициирует pipeline")
Rel(gen, scaffold, "Запрашивает scaffold output decisions")
Rel(gen, runtime_adapter, "Экспортирует operation/openapi metadata")
Rel(config, fs, "Читает config и пишет валидированные параметры")
Rel(scaffold, fs, "Пишет scaffold в независимый root с политикой записи")
Rel(gen, fs, "Пишет generated artifacts")
Rel(runtime_adapter, runtime, "Передает normalized add_api_route payload")
```

## C4 Level 3: Component
```mermaid
C4Component
title Integration Components (L3)
Container_Boundary(integration_components, "Integration Core Components") {
  Component(path_policy, "Path Boundary Policy", "Security Policy", "Независимое разрешение generated_dir/scaffold_dir в рамках project-root")
  Component(scaffold_policy, "Scaffold Write Policy Resolver", "Policy Engine", "create-missing / skip-existing / fail-on-conflict")
  Component(route_adapter, "Route Projection Adapter", "Runtime Adapter", "Проецирует operation map в runtime route descriptors")
  Component(openapi_adapter, "OpenAPI Projection Adapter", "Runtime Adapter", "Проецирует summary/description/errors/tags/extensions")
  Component(error_example_normalizer, "Error Example Normalizer", "Contract Normalization", "Сводит short-form и nested example в каноническую форму")
  Component(init_profile_resolver, "Init Integration Profile Resolver", "CLI Profile Model", "Разворачивает profile/runtime/mode/dir в предсказуемый набор артефактов")
  Component(extension_toggle, "OpenAPI Extension Toggle", "Config Gate", "Управляет включением x-apidev-* без изменения базовой семантики")
}

Rel(path_policy, scaffold_policy, "Передает разрешенные output boundaries")
Rel(error_example_normalizer, openapi_adapter, "Передает normalized error payload")
Rel(route_adapter, openapi_adapter, "Разделяет единый источник operation metadata")
Rel(extension_toggle, openapi_adapter, "Фильтрует extension fields на этапе проекции")
```

## Архитектурные инварианты
- Любая запись остается в пределах `project-root`; выход за границы и неоднозначные пути запрещены.
- `scaffold_dir` независим от `generated_dir` логически, но подчиняется тем же security boundary правилам.
- Порядок обработки операций стабилен и не зависит от окружения запуска.
- Runtime route metadata и OpenAPI metadata получают данные из единой нормализованной модели.
- Домен endpoint-а определяется из domain layout операции; Swagger tags являются производным представлением, а не отдельным источником истины.
- Отключение OpenAPI extensions влияет только на `x-apidev-*` поля и не меняет core OpenAPI семантику.
