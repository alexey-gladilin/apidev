# Integration Contract: Generated Transport + Manual App Layer

## Цель
Зафиксировать целевой способ интеграции generated артефактов APIDev в runtime target приложения без переноса ownership бизнес-логики в generated-зону.

## Ownership
- Generated: transport metadata, route adapters, model artifacts, OpenAPI builder.
- Manual: business handlers, auth dependencies/policy, error mapping policy, application composition root.

## Binding Pattern
- Registry (`operation_map.py`) предоставляет operation metadata.
- Factory (manual) регистрирует FastAPI endpoints и связывает metadata с ручными handler/auth/error компонентами.

## Integration Sequence
```mermaid
sequenceDiagram
    participant CR as Composition Root (manual)
    participant OPM as operation_map.py (generated)
    participant RF as RouterFactory (manual)
    participant HR as HandlerRegistry (manual)
    participant AR as AuthRegistry (manual)
    participant ER as ErrorMapper (manual)
    participant RT as <domain>/routes/<operation>.py (generated)

    CR->>RF: build_router()
    RF->>OPM: read OPERATION_MAP
    loop each operation
        RF->>HR: resolve(operation_id)
        RF->>AR: resolve(auth)
        RF->>RT: bind route(payload, handler)
        RF->>ER: attach error policy wrapper
        RF-->>CR: add_api_route(path, method, endpoint)
    end
```

## OpenAPI Contract
- `openapi_docs.py` детерминированно строит `paths` фрагмент из generated registry.
- Composition root target app решает, как объединять этот фрагмент с runtime OpenAPI schema.

## Негативные границы
- Generated layer не реализует business handlers.
- Generated layer не реализует project-specific auth policy.
- Generated layer не реализует domain-specific error semantics.
