# Decisions

## D1. Write ownership только у `gen apply`
- Решение: release-state auto-create/sync выполняется только в `apidev gen` без `--check`.
- Причина: сохранить read-only контракт `diff` и `gen --check`.

## D2. Bump policy привязан к фактическому apply
- Решение: `release_number` увеличивается только при реально примененных изменениях.
- Причина: исключить ложный рост релизного номера на no-op запусках.

## D3. Baseline precedence не меняется
- Решение: сохранить `CLI -> release-state -> git fallback`.
- Причина: совместимость с текущим поведением compare pipeline и тестовыми контрактами.

## D4. Write-after-success
- Решение: sync release-state выполняется после успешного завершения apply.
- Причина: не фиксировать новый release-state при частичных/ошибочных apply.

## D5. Документируем no-git behavior без скрытого auto-fix в read-only
- Решение: при no-git сохраняется диагностируемое поведение baseline resolve.
- Причина: прозрачность и предсказуемость CI/локальных запусков.
