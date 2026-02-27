# Phase 02 - Generation and OpenAPI Propagation

## Цель

Сделать schema-level и endpoint-level examples частью deterministic generation metadata и generated OpenAPI transport артефактов.

## Work packages

1. Проверить и при необходимости обновить fingerprint payload с учетом examples.
2. Расширить transport schema template для экспонирования examples.
3. Расширить openapi docs template для включения operation-level request/response/error examples.

## Deliverables

- `src/apidev/application/services/diff_service.py`
- `src/apidev/templates/generated_schema.py.j2`
- `src/apidev/templates/generated_openapi_docs.py.j2`

## Exit criteria

- Изменение `example` отражается в diff/gen output.
- Изменение endpoint-level `examples` отражается в diff/gen output.
- При неизменных входах generated output остается byte-stable.
