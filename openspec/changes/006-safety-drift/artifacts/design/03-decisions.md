# Решения и компромиссы

## Decision 1: `REMOVE` как first-class change type
- Решение: расширить generation plan явной поддержкой `REMOVE`.
- Причина: drift должен отражать не только появление/обновление, но и удаление stale generated artifacts.
- Компромисс: увеличивается сложность apply-пайплайна и тестовой матрицы.

## Decision 2: Единая drift-логика для `diff` и `gen --check`
- Решение: drift detection использует единый предикат по типам `ADD|UPDATE|REMOVE`.
- Причина: устранение рассинхронизации preview/check и CI-gate.
- Компромисс: потребуется обновление существующих тестов и CLI-сообщений.

## Decision 3: Boundary enforcement обязателен и для remove
- Решение: операции удаления проходят те же ограничения generated-root, что и запись.
- Причина: сохранение ownership boundary и предотвращение удаления manual файлов.
- Компромисс: часть конфликтов (например, path traversal) становится hard-fail.

## Decision 4: Deterministic diagnostics для remove-case
- Решение: фиксировать machine-readable коды remove-конфликтов и boundary-нарушений.
- Причина: CI triage и воспроизводимость сигналов.
- Компромисс: расширение diagnostic контракта в коде и документации.

## Альтернативы, которые рассмотрены
- Не включать `REMOVE` в drift и оставить только apply-семантику.
  - Отклонено: не решает CI drift-gap для stale artifacts.
- Выполнять auto-clean без explicit `REMOVE` в плане.
  - Отклонено: снижает наблюдаемость и воспроизводимость.

## Риски и митигации
- Риск: случайное удаление нужного generated файла из-за ошибки в expected set.
  - Митигация: deterministic expected-set builder + regression suite.
- Риск: несовместимость CLI-контракта при изменении сообщений.
  - Митигация: синхронное обновление `docs/reference/cli-contract.md` и CLI tests.
