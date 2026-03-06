# Решения и Trade-offs: Diff/Generate Safety

## Decision 1: Safety pipeline как единый контракт `validate -> diff -> gen` (`REQ-1`, `REQ-2`)

- Контекст: baseline реализует шаги, но без формализованного capability-контракта.
- Решение: закрепить последовательность и режимы как обязательную архитектурную норму.
- Trade-off: меньше свободы для локальных оптимизаций, но выше предсказуемость CI-поведения.

## Decision 2: Read-only governance для preview/check (`REQ-2`)

- Контекст: drift-gate должен быть безопасным для workspace.
- Решение: запретить запись в `diff` и `gen --check` как контракт, а не как incidental behavior.
- Trade-off: дополнительные проверки non-mutation в тестах, но лучше защищается ручной код и окружение разработчика.

## Decision 3: Централизованный write-boundary через `SafeWriter` (`REQ-3`)

- Контекст: главный риск этапа C — случайная модификация manual-owned зоны.
- Решение: сохранять единую точку контроля записи и отклонять любые boundary violations.
- Trade-off: часть edge-cases требует явного конфигурирования generated-root, но это уменьшает blast radius ошибок.

## Decision 4: Determinism как first-class требование drift governance (`REQ-4`)

- Контекст: нестабильный порядок операций порождает flaky drift в CI.
- Решение: фиксировать детерминированное построение и ordering diff-плана как контракт.
- Trade-off: ограничение на потенциально более быстрые, но недетерминированные алгоритмы.

## Decision 5: Spec-driven traceability между design и delta requirements (`REQ-1..REQ-4`)

- Контекст: этап C требует проверяемости governance-правил до implement-фазы.
- Решение: каждое архитектурное/поведенческое решение маркируется связью с requirement ID.
- Trade-off: больше документационной дисциплины, но проще ревью и приемка.

## Assumptions

- Переиспользование текущих сервисов дешевле и безопаснее, чем архитектурный redesign.
- Ключевые failure-modes уже известны из baseline и могут быть покрыты тестами без расширения scope.
- Команда согласует единый словарь терминов: drift, check-mode, apply-mode, boundary violation.

## Unresolved Questions

- Нужно ли ввести формальный ADR-шаблон для будущих governance-изменений.
- Следует ли выделить отдельный ownership policy-документ, если boundary-правила будут расширяться.
- Нужны ли отдельные решения по миграции старых generated artifacts при ужесточении policy.
