# Архитектура: Request Contract Extension (`013-extend-contract`)

## Контекст
Baseline показал, что текущая модель контракта покрывает `response` и `errors`, но не содержит нормативного root-блока `request`. Из-за этого request-часть transport/OpenAPI не генерируется детерминированно и остается эвристической/пустой.

## Архитектурные цели
- Добавить в контракт явный schema-driven слой request-модели.
- Сохранить strict schema validation и fail-fast diagnostics.
- Синхронизировать request-представление между validation, operation metadata и OpenAPI projection.
- Сохранить детерминированность генерации при одинаковом входе.

## C4 Level 1: System Context
```mermaid
C4Context
title APIDev Request Contract Extension (L1)
Person(dev, "Developer / CI", "Пишет YAML-контракты и запускает validate/gen")
System(apidev, "apidev CLI", "Валидирует контракты и генерирует артефакты")
System_Ext(repo, "Project Repository", "contracts, config, generated artifacts")
System_Ext(consumers, "Runtime + OpenAPI Consumers", "Используют operation metadata и OpenAPI")

Rel(dev, apidev, "Запускает validate/gen")
Rel(apidev, repo, "Читает контракты, пишет generated artifacts")
Rel(apidev, consumers, "Публикует request/response metadata и OpenAPI projection")
```

## C4 Level 2: Container
```mermaid
C4Container
title APIDev Containers for Request Extension (L2)
Person(dev, "Developer / CI")
System_Boundary(apidev_boundary, "apidev") {
  Container(cli, "CLI Layer", "Typer", "Entry points validate/gen/diff")
  Container(schema_validation, "Contract Schema Validation", "Rules + Diagnostics", "Проверка структуры request/path/query/body и unknown fields")
  Container(contract_model, "Contract Model Layer", "Core Models", "Нормализованное представление EndpointContract с request-секцией")
  Container(generation, "Generation Pipeline", "Application Services", "Формирует operation_map, transport metadata и OpenAPI projection")
  Container(templates, "Template Projection", "Jinja templates", "Генерирует operation_map/openapi/request-model artifacts")
}
System_Ext(repo, "Filesystem / Repository")
System_Ext(openapi, "OpenAPI Consumers")

Rel(dev, cli, "Команды")
Rel(cli, schema_validation, "Валидация контрактов")
Rel(schema_validation, contract_model, "Передает валидную модель")
Rel(contract_model, generation, "Передает canonical endpoint model")
Rel(generation, templates, "Проецирует metadata в артефакты")
Rel(schema_validation, repo, "Читает контракт YAML")
Rel(templates, repo, "Пишет generated files")
Rel(generation, openapi, "Поставляет OpenAPI-compatible request projection")
```

## C4 Level 3: Component
```mermaid
C4Component
title Request Extension Components (L3)
Container_Boundary(request_extension, "Request Contract Extension Components") {
  Component(root_request_gate, "Request Root Gate", "Schema Rule", "Разрешает root `request` и запрещает неизвестные поля")
  Component(path_param_consistency, "Path Param Consistency Validator", "Validation Rule", "Согласует `request.path` и `{param}` в route path")
  Component(query_schema_validator, "Query Schema Validator", "Validation Rule", "Проверяет `request.query` как schema fragment")
  Component(body_schema_validator, "Body Schema Validator", "Validation Rule", "Проверяет `request.body` как schema fragment")
  Component(request_model_mapper, "Request Model Mapper", "Model Mapping", "Расширяет EndpointContract request-полями")
  Component(operation_request_metadata, "Operation Request Metadata Projector", "Generation Step", "Публикует path/query/body fragments в operation_map")
  Component(openapi_request_projector, "OpenAPI Request Projector", "Generation Step", "Строит `parameters` и `requestBody` из request metadata")
  Component(request_transport_projector, "Request Transport Projector", "Generation Step", "Формирует request model вместо пустого `{}`")
}

Rel(root_request_gate, request_model_mapper, "Передает валидный request block")
Rel(path_param_consistency, request_model_mapper, "Передает согласованный path params set")
Rel(query_schema_validator, request_model_mapper, "Передает validated query fragment")
Rel(body_schema_validator, request_model_mapper, "Передает validated body fragment")
Rel(request_model_mapper, operation_request_metadata, "Источник нормализованной request-модели")
Rel(operation_request_metadata, openapi_request_projector, "Передает path/query/body metadata")
Rel(operation_request_metadata, request_transport_projector, "Передает schema fragments для transport-model")
```

## Архитектурные инварианты
- `request` обрабатывается как нормативная часть root-контракта.
- Unknown fields в `request` и его подблоках запрещены.
- `request.path` должен быть строго согласован с route path placeholders.
- `request.query` и `request.body` опциональны, но при наличии обязаны быть валидными schema fragments.
- `operation_map` становится единой точкой request metadata для downstream проекций.
- OpenAPI `parameters`/`requestBody` строятся только из контрактной request-модели, без эвристик.
- Генерация и диагностика остаются детерминированными.
