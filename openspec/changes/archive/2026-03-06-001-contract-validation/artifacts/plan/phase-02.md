# Phase 02 — Semantic Validation & Diagnostic Codes

## Scope
- Зафиксировать semantic checks поверх schema-валидных контрактов.
- Определить стабильный каталог diagnostic codes и severity policy.
- Подготовить deterministic ordering policy для diagnostics.

## Deliverables
- Таблица semantic rules (включая duplicate `operation_id`).
- Каталог diagnostic codes с namespace и описанием.
- Набор unit/contract тестов на semantic violations.

## Verification
- `pytest tests/unit -k validate`
- `pytest tests/unit -k operation_id`
- `ruff check src tests`
- Stability review diagnostics ordering on repeated runs

## Definition of Done
- Каждому semantic rule соответствует стабильный diagnostics code.
- Различимость schema/semantic ошибок формализована через `rule`/`code`.
- Подготовлены тестовые сценарии на коллизии и межконтрактные инварианты.
