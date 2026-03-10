## 1. Формат и спецификация
- [ ] 1.1 Зафиксировать canonical operation metadata contract для `intent` и `access_pattern` в spec delta и proposal/design. DoD: допустимые значения, compatibility matrix и mandatory-field policy описаны без двусмысленности.
- [ ] 1.2 Синхронизировать `docs/reference/contract-format.md`, `docs/reference/cli-contract.md` и authoring examples с новым SSOT metadata contract. DoD: docs показывают explicit `POST`-read и `POST`-write сценарии.

## 2. Валидация и ingest
- [ ] 2.1 Обновить contract models / YAML loader для поддержки новых root-level operation fields. DoD: parse stage принимает explicit metadata и не подставляет implicit defaults.
- [ ] 2.2 Добавить semantic validation для allowed values и forbidden combinations `intent/access_pattern`. DoD: validate возвращает stable diagnostics для invalid combinations.
- [ ] 2.3 Добавить validation на отсутствие обязательных `intent` и `access_pattern`. DoD: legacy contracts без новых полей детерминированно отклоняются с machine-readable diagnostics.

## 3. Generated metadata и downstream contract
- [ ] 3.1 Расширить operation registry / generated metadata новыми полями `intent` и `access_pattern`. DoD: operation map и related generated metadata публикуют SSOT значения детерминированно.
- [ ] 3.2 Добавить OpenAPI vendor extensions для новых metadata. DoD: generated OpenAPI содержит `x-apidev-intent` и `x-apidev-access-pattern`.
- [ ] 3.3 Зафиксировать downstream-facing contract так, чтобы consumer tools могли различать semantic read/write и cached/imperative usage без локальных эвристик. DoD: examples и tests показывают usable metadata contract.

## 4. Верификация
- [ ] 4.1 Добавить unit/contract tests на explicit valid combinations `read+cached`, `read+imperative`, `read+both`, `write+imperative`, `write+none`. DoD: tests подтверждают allowed matrix.
- [ ] 4.2 Добавить negative tests на invalid combinations, invalid enum values и missing required metadata. DoD: diagnostics machine-readable и deterministic.
- [ ] 4.3 Добавить integration tests на generated operation map/OpenAPI vendor extensions и migration failures для legacy contracts. DoD: repo-level generation tests подтверждают explicit metadata contract и deterministic rejection legacy mode.
- [ ] 4.4 Прогнать обязательные quality gates `uv run pytest` и `openspec validate add-operation-intent-metadata --strict --no-interactive`. DoD: оба gate проходят.

## 5. Handoff
- [ ] 5.1 Подготовить implementation handoff с migration notes для downstream consumers (`uidev` и другие). DoD: handoff перечисляет field contract, migration expectations и residual risks.
