# Change: Дополнительные аргументы include/exclude endpoint для `apidev gen`

## Почему
Сейчас `apidev gen` всегда обрабатывает полный набор контрактов, что усложняет частичную генерацию при локальной разработке, точечных правках и поэтапном rollout по доменам.
Нужен явный CLI-контракт для выборочной генерации endpoint-ов через include/exclude фильтры без нарушения детерминированности.

## Что изменится
- Добавляется CLI-возможность фильтрации endpoint-ов для `apidev gen`:
  - `--include-endpoint <pattern>` (множественный флаг);
  - `--exclude-endpoint <pattern>` (множественный флаг).
- Формализуется precedence и семантика фильтров:
  - include формирует исходный candidate set;
  - exclude вычитает endpoint-ы из candidate set;
  - при пустом include берется полный набор контрактов.
- Формализуется поведение диагностики:
  - детерминированная ошибка при пустом effective set (когда после фильтров не осталось endpoint-ов);
  - детерминированная ошибка при невалидном паттерне фильтра.
- Обновляется CLI/UX контракт и требования к тестированию для фильтрации endpoint-ов.

## Влияние
- Затронутые спеки: `cli-tool-architecture` (ADDED requirement).
- Затронутый код (на implement-фазе):
  - `src/apidev/commands/generate_cmd.py`
  - `src/apidev/application/services/generate_service.py`
  - `src/apidev/application/services/diff_service.py` (фильтрация списка операций перед построением плана)
  - `docs/reference/cli-contract.md`
  - `tests/unit/**`, `tests/integration/**`
- Breaking:
  - нет; существующий запуск `apidev gen` без новых флагов остается совместимым.

## Linked Artifacts
- Research: [artifacts/research/2026-03-03-endpoint-filtering-baseline.md](./artifacts/research/2026-03-03-endpoint-filtering-baseline.md)
- Design package: [artifacts/design/README.md](./artifacts/design/README.md)
- Plan package: [artifacts/plan/README.md](./artifacts/plan/README.md)
- Spec delta: [specs/cli-tool-architecture/spec.md](./specs/cli-tool-architecture/spec.md)

## Границы этапа
Этот change описывает только proposal/design/plan и не включает production-реализацию.
Implement выполняется отдельной командой (`/openspec-implement` или `/openspec-implement-single`) после approval.
