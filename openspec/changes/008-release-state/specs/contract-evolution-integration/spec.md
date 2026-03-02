## MODIFIED Requirements

### Requirement: Контракт хранения release state и границы ответственности
Система SHALL использовать явный источник истины для release state и SHALL исключать неявные side effects в read-only режимах.

#### Scenario: Источник истины задаётся через конфиг с документированным default
- **WHEN** пользователь не задаёт override для release state storage
- **THEN** система SHALL читать release state из `.apidev/release-state.json` по умолчанию
- **AND** путь MAY быть переопределён через `.apidev/config.toml` в секции `evolution.release_state_file`

#### Scenario: Формат release state фиксирован и валидируется
- **WHEN** система читает `.apidev/release-state.json`
- **THEN** файл SHALL быть JSON-объектом формата:
  `{ "release_number": <int>=1..N, "baseline_ref": "<git-tag|git-sha>", "released_at": "<RFC3339 UTC>"?, "git_commit": "<40-hex>"?, "tag": "<string>"? }`
- **AND** при нарушении формата система SHALL возвращать ошибку конфигурации с указанием некорректного поля

#### Scenario: Read-only режимы не модифицируют release state
- **WHEN** запускается `apidev diff` или `apidev gen --check`
- **THEN** система SHALL NOT изменять release state storage
- **AND** любые ошибки чтения/валидации release state SHALL отражаться в diagnostics без скрытой записи на диск

#### Scenario: `apidev gen` автоматически bootstrap'ит release-state при отсутствии файла
- **WHEN** пользователь запускает `apidev gen` (без `--check`) и release-state файл отсутствует
- **THEN** система SHALL создать release-state JSON в configured location
- **AND** созданный release-state SHALL содержать валидные обязательные поля `release_number` и `baseline_ref`

#### Scenario: No-git/no-baseline в apply-режиме обрабатывается детерминированно без записи
- **WHEN** пользователь запускает `apidev gen` (без `--check`), `--baseline-ref` не задан, release-state отсутствует или не содержит валидный `baseline_ref`, и git fallback недоступен
- **THEN** система SHALL вернуть diagnostic `baseline-missing` или `baseline-invalid` согласно причине
- **AND** система SHALL NOT создавать или изменять release-state storage в этом запуске

### Requirement: Формальный deprecation lifecycle и release state
Система SHALL обеспечивать формальный deprecation lifecycle (`active -> deprecated -> removed`) с релизным состоянием, достаточным для проверки deprecation window.

#### Scenario: Deprecated элемент отслеживается до удаления
- **WHEN** элемент контракта помечается как `deprecated`
- **THEN** diagnostics и generated metadata SHALL отображать deprecation status
- **AND** lifecycle state SHALL сохраняться между последующими запусками diff/generate

#### Scenario: Release state использует монотонный номер релиза
- **WHEN** система загружает release state для policy checks
- **THEN** release state SHALL включать обязательный `release_number` (integer, монотонно возрастающий)
- **AND** release state MAY включать `git_commit`, `released_at` (UTC) и `tag` как опциональные metadata для трассировки

#### Scenario: `apidev gen` увеличивает `release_number` при применении изменений
- **WHEN** пользователь запускает `apidev gen` (без `--check`) и generation plan содержит хотя бы одно изменение `ADD|UPDATE|REMOVE`
- **THEN** система SHALL увеличить `release_number` в release-state на `1`
- **AND** если generation plan не содержит применённых изменений, `release_number` SHALL оставаться неизменным

#### Scenario: Приоритет baseline_ref сохраняется при auto-sync release-state
- **WHEN** пользователь запускает `apidev gen` с/без `--baseline-ref`
- **THEN** приоритет `baseline_ref` SHALL оставаться `CLI override -> release-state -> git fallback`
- **AND** итоговое значение `baseline_ref` SHALL синхронизироваться в release-state только в apply-режиме
