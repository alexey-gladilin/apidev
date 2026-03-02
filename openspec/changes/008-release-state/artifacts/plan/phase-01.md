# Phase 01 - Release-State Lifecycle Core

## Scope
- Определить и реализовать lifecycle hooks в apply-mode `GenerateService`.
- Зафиксировать policy bump/no-bump для `release_number`.
- Зафиксировать baseline precedence для sync payload.

## Outputs
- `src/apidev/application/services/generate_service.py`
- `src/apidev/core/models/release_state.py` (только при необходимости расширения контракта)
- `tests/unit/**`

## Verification
- `uv run pytest tests/unit -k "generate_service and release_state"`

## Definition of Done
- `gen apply` создает release-state при отсутствии.
- `release_number` увеличивается только при примененных изменениях.
- write выполняется только после успешного apply.
