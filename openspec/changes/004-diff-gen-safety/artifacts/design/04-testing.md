# Тестирование: Diff/Generate Safety & Drift Governance

## 1. Цели тестирования

- Подтвердить `REQ-1`: validate-first блокирует diff/apply при невалидном входе.
- Подтвердить `REQ-2`: preview/check режимы остаются non-mutating.
- Подтвердить `REQ-3`: write-boundary жестко ограничивает зону записи.
- Подтвердить `REQ-4`: drift signal и ordering детерминированы.

## 2. Матрица покрытия spec delta

- `REQ-1` Validate-First Safety Pipeline  
  Unit: отказ при validation failure до планирования.  
  Integration: `diff` и `gen` завершаются с ожидаемым failure-signal.
- `REQ-2` Drift Governance Modes  
  Unit: `check=True` не вызывает writer-path.  
  Contract: `diff`/`gen --check` не меняют snapshot файлов.  
  Integration: drift detected/no-drift сценарии для check/apply.
- `REQ-3` Generated Write Boundary Safety  
  Unit: отклонение пути вне root.  
  Unit: отклонение записи в `generated-root` как файл.  
  Contract: manual-owned файлы неизменны после apply/check.
- `REQ-4` Deterministic Drift Signal  
  Unit: стабильная сортировка операций.  
  Integration: повторный run на неизменных входах дает эквивалентный результат и отсутствие новых изменений после apply.

## 3. Набор обязательных сценариев

- Negative safety: invalid contracts/config -> execution blocked before planning/apply.
- Non-mutation proof: `diff` и `gen --check` с filesystem snapshot/spy.
- Boundary violation: write target outside root -> explicit safety error.
- Deterministic replay: одинаковый вход -> одинаковый план/статус.
- Metadata drift: изменение contract-significant metadata -> drift, затем no-drift после apply.

## 4. Рекомендуемые test layers

- Unit: сервисная логика `DiffService`, `GenerateService`, `SafeWriter`.
- Contract: инварианты архитектуры безопасности и ownership boundary.
- Integration: end-to-end `validate -> diff -> gen --check -> gen` на фикстурах контрактов.

## 5. Quality gates для implement-фазы

- Ни один requirement из `REQ-1..REQ-4` не остается без автоматизированного сценария.
- Есть отдельные тесты на non-mutation для `diff` и `gen --check`.
- Regression-набор детектирует нарушения детерминизма и boundary-policy.
- Тесты стабильны в CI, без flaky drift-сценариев.

## Assumptions

- Существующая тестовая инфраструктура поддерживает snapshot/spy подход для filesystem assertions.
- Текущие фикстуры контрактов покрывают базовые и metadata-driven кейсы.
- CI окружение выполняет тесты в изолированном workspace.

## Unresolved Questions

- Нужно ли сделать отдельный `tests/contract/diff_gen_safety/` пакет как обязательную структуру.
- Следует ли стандартизовать формат assertion для drift-status между unit и integration слоями.
- Нужен ли performance-smoke тест на больших контрактах в scope этого change.
