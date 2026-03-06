# Тестирование: include/exclude endpoint

## Цели тестирования
- Подтвердить корректный parsing и валидацию новых CLI-флагов.
- Подтвердить deterministic endpoint selection в generation pipeline.
- Подтвердить стабильные diagnostics для error-path фильтрации.

## Unit tests
- CLI parser:
  - множественные `--include-endpoint`/`--exclude-endpoint`;
  - пустые и malformed glob pattern (включая незакрытый `[` character-class);
  - expected mapping в service-вызов.
- Diff/Generate selection:
  - include-only;
  - exclude-only;
  - include+exclude c overlap;
  - stable ordering selected operations.

## Integration tests
- `apidev gen --check` с include/exclude:
  - drift/no-drift сценарии;
  - JSON envelope с filter diagnostics при ошибке и `generation.*` code namespace.
- `apidev gen` apply:
  - проверка apply/remove в границах filtered scope;
  - проверка, что remove не затрагивает endpoint-ы вне effective endpoint set.
  - отсутствие write boundary violations.

## Regression guards
- Без новых флагов поведение `apidev gen` остается неизменным.
- Существующие diagnostics/exit semantics для не связанных сценариев не деградируют.

## Acceptance mapping к spec
- Requirement "Endpoint Include/Exclude Selection for Code Generation":
  - Scenario: pattern grammar и matching policy детерминированы.
  - Scenario: include ограничивает набор endpoint-ов.
  - Scenario: exclude исключает endpoint-ы после include.
  - Scenario: invalid pattern вызывает ошибку с diagnostics.
  - Scenario: empty effective set возвращает fail-fast diagnostics.
  - Scenario: remove-semantics ограничена выбранным endpoint scope.
  - Scenario: отсутствие фильтров сохраняет backward-compatible поведение.
