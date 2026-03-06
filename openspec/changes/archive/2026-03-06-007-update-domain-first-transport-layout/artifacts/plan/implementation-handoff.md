# Implementation Handoff

## Scope Summary
Реализовать domain-first generated layout для transport artifacts как новый canonical output.

## Основные deliverables
- обновленный generation path planner;
- обновленные templates и registry metadata paths;
- актуализированные tests/docs.

## Guardrails
- не нарушать write-boundary policy;
- не менять ownership границу generated/manual;
- сохранить стабильность `operation_id`.

## Verification
- unit + contract + integration test matrix;
- `openspec validate update-domain-first-transport-layout --strict --no-interactive`.

## Ownership Gate Checklist
- Generated-only (overwrite allowed): `operation_map.py`, `openapi_docs.py`, `<domain>/routes/*`, `<domain>/models/*`.
- Generated scaffold (create-if-missing only): `<scaffold_dir>/handler_registry.py`, `router_factory.py`, `auth_registry.py`, `error_mapper.py`.
- Manual-only (never overwritten): business handlers, auth/token decode policy, app composition/factory wiring, project-specific error mapping.
