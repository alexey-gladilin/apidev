# Phase 02 - Generation and OpenAPI Propagation

## Цель

Сделать schema-level `example` частью deterministic generation metadata и generated OpenAPI transport артефактов.

## Work packages

1. Проверить и при необходимости обновить fingerprint payload с учетом `example`.
2. Расширить transport schema template для экспонирования `example`.
3. Расширить openapi docs template для включения schema-level `example` в response/error metadata.

## Deliverables

- `src/apidev/application/services/diff_service.py`
- `src/apidev/templates/generated_schema.py.j2`
- `src/apidev/templates/generated_openapi_docs.py.j2`

## Exit criteria

- Изменение `example` отражается в diff/gen output.
- Root-level `examples` не появляется в generated output и остается вне scope.
- При неизменных входах generated output остается byte-stable.
