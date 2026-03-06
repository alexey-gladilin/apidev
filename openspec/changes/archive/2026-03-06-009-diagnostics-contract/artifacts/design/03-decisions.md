# Decisions and Trade-offs

## D1. Единый JSON envelope для всех CLI режимов
- Решение: ввести общий формат machine-readable payload для `validate|diff|gen --check|gen`.
- Причина: CI/automation нуждается в стабильном parse contract.
- Компромисс: требуется согласованный mapper для разнородных diagnostics DTO.

## D2. Минимально-обязательное ядро diagnostics fields
- Решение: обязательные `code|severity|location|message`; остальное опционально.
- Причина: сохранить совместимость и снизить migration cost.
- Компромисс: часть domain-specific контекста остается в optional fields.

## D3. Namespace-политика кодов
- Решение: `validation.*`, `compatibility.*`, `generation.*`, `runtime.*`, `config.*`.
- Причина: убрать коллизии и упростить маршрутизацию в triage/analytics.
- Компромисс: потребуется миграция legacy code names к каноническому виду.

## D4. Plain-text output сохраняется
- Решение: JSON контракт добавляется как explicit machine-readable mode, text остается дефолтом.
- Причина: не ломать текущий UX и привычный локальный workflow.
- Компромисс: две формы представления требуют синхронного тестового покрытия.

## D5. Drift/policy semantics не трогаем в этом change
- Решение: не менять бизнес-логику classify/drift/exit, только контракт представления diagnostics.
- Причина: ограничить риск регрессий и удержать scope Horizon 1.
- Компромисс: отдельные улучшения policy-сигналов выносятся в последующие change-пакеты.
