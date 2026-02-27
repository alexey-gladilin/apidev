# Change: Этап A — Contract Validation Hardening

## Why
Текущее состояние `apidev validate` ограничено базовой загрузкой YAML-контрактов и проверкой уникальности `operation_id`.
Этого недостаточно для целевого состояния из `docs/roadmap.md`: строгая схема контракта, семантические проверки, диагностические коды и машиночитаемый `--json` вывод.

## What Changes
- Добавляется capability `contract-validation-hardening` с формализованными требованиями к strict schema validation.
- Формализуется слой semantic validation для контрактов поверх структурной проверки.
- Формализуется единый структурированный формат diagnostics (включая стабильные diagnostic codes).
- Формализуется dual-mode вывод `apidev validate`: human-readable (по умолчанию) и JSON (`--json`).
- Уточняется контракт exit code для validation failures без изменения базового UX команды.

## Impact
- Affected specs: `contract-validation-hardening` (new)
- Affected code (target for implement phase): `src/apidev/application/services/validate_service.py`, `src/apidev/application/dto/diagnostics.py`, `src/apidev/commands/validate_cmd.py`, `src/apidev/core/rules/**`, `src/apidev/infrastructure/contracts/yaml_loader.py`, `tests/**`
- Breaking: нет (расширение поведения validate без удаления текущей команды)

## Linked Artifacts
- Research: [artifacts/research/2026-02-27-contract-validation-baseline.md](./artifacts/research/2026-02-27-contract-validation-baseline.md)
- Design package: [artifacts/design/README.md](./artifacts/design/README.md)
- Plan package: [artifacts/plan/README.md](./artifacts/plan/README.md)
