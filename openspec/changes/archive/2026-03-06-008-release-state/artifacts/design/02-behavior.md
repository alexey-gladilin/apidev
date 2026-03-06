# Behavior Contract: release-state auto-create/sync

## Режимы команд

- `apidev diff`: read-only; release-state только читается/валидируется.
- `apidev gen --check`: read-only; release-state только читается/валидируется.
- `apidev gen`: apply mode; после успешного apply разрешен auto-create/sync release-state.

## Baseline precedence

Для apply-mode и compatibility compare сохраняется порядок:

1. CLI override `--baseline-ref`.
2. `release-state.baseline_ref`.
3. git fallback (deterministic ref from current repo context).

## Auto-create release-state

- Если configured release-state отсутствует и выполняется `gen` apply:
  - создается валидный JSON object;
  - обязательные поля: `release_number >= 1`, `baseline_ref`.

## Auto-update release_number

- Если в `gen` apply есть примененные изменения (`ADD|UPDATE|REMOVE`), `release_number` увеличивается на `1`.
- Если примененных изменений нет, `release_number` остается прежним.

## No-git / missing baseline behavior

- Если baseline не удается резолвить для compare, формируются `baseline-missing` или `baseline-invalid`.
- Неуспешный VCS-resolve не должен приводить к скрытым write в read-only режимах.

## Error semantics

- Невалидный release-state отражается в diagnostics как `release-state-invalid`.
- Ошибка apply должна оставлять release-state без частично примененной мутации.

