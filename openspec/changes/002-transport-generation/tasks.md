## 1. Planning — Phase 01 (Generation Surface & Contracts)

- [x] 1.1 Scope: зафиксировать целевой состав generated transport-артефактов (registry/router/models/errors); Output: [artifacts/plan/phase-01.md](./artifacts/plan/phase-01.md); Verification: traceability review against [specs/transport-generation/spec.md](./specs/transport-generation/spec.md); DoD: определен полный artifact inventory и ownership boundary.
- [x] 1.2 Scope: зафиксировать contract operation registry (структура, стабильность, deterministic ordering); Output: [artifacts/design/02-behavior.md](./artifacts/design/02-behavior.md); Verification: cross-check with [artifacts/design/03-decisions.md](./artifacts/design/03-decisions.md); DoD: описан стабильный registry contract для runtime/CI.
- [x] 1.3 Scope: зафиксировать bridge contract между generated transport и manual handlers; Output: [artifacts/plan/phase-01.md](./artifacts/plan/phase-01.md); Verification: architecture review against [artifacts/design/01-architecture.md](./artifacts/design/01-architecture.md); DoD: определены callable signatures и ответственность слоев.

## 2. Planning — Phase 02 (Template Architecture & Safety)

- [x] 2.1 Scope: декомпозировать шаблоны генерации для request/response/error моделей и router wiring; Output: [artifacts/plan/phase-02.md](./artifacts/plan/phase-02.md); Verification: mapping review to existing templates `src/apidev/templates/*.j2`; DoD: есть план миграции шаблонов без нарушения deterministic output.
- [x] 2.2 Scope: зафиксировать safety-инварианты generated/manual границы и write-boundary; Output: [artifacts/design/03-decisions.md](./artifacts/design/03-decisions.md); Verification: alignment check with `docs/architecture/architecture-rules.md`; DoD: документированы запреты на генерацию бизнес-логики и ручных зон.
- [x] 2.3 Scope: сформировать acceptance-критерии для минимально runnable transport layer; Output: [artifacts/design/02-behavior.md](./artifacts/design/02-behavior.md); Verification: scenario review against spec delta; DoD: определены runnable условия для endpoint skeleton без ручного переписывания generated-кода.

## 3. Planning — Phase 03 (Verification & Handoff)

- [x] 3.1 Scope: зафиксировать тестовую матрицу unit/contract/integration для transport generation MVP+; Output: [artifacts/design/04-testing.md](./artifacts/design/04-testing.md); Verification: planned commands `uv run pytest tests/unit tests/contract tests/integration`; DoD: описаны обязательные positive/negative/regression сценарии.
- [x] 3.2 Scope: описать пошаговый implement-handoff с зависимостями фаз `P1 -> P2 -> P3`; Output: [artifacts/plan/implementation-handoff.md](./artifacts/plan/implementation-handoff.md); Verification: dependency review with [artifacts/plan/README.md](./artifacts/plan/README.md); DoD: зафиксирован последовательный roadmap без неоднозначностей.
- [x] 3.3 Scope: синхронизировать links между proposal/design/tasks/specs/artifacts и выполнить strict validation; Output: [artifacts/plan/README.md](./artifacts/plan/README.md); Verification: `openspec validate 002-transport-generation --strict --no-interactive`; DoD: change-пакет валиден и готов к отдельной implement-команде.

## 4. Implementation — Phase B (Transport Generation MVP+)

- [x] 4.1 Расширить generation plan в `src/apidev/application/services/diff_service.py`: добавить deterministic generation для `transport/models/*` (request/response/error) и расширить metadata в `operation_map.py`; Verification: unit tests на стабильный набор и порядок артефактов.
- [x] 4.2 Обновить шаблоны `src/apidev/templates/*.j2` для minimal runnable transport layer: router wiring + явный bridge contract к manual handlers без бизнес-логики; Verification: integration test runnable skeleton и проверка сигнатур bridge.
- [x] 4.3 Гарантировать stable operation registry contract (`operation_id -> method/path + refs на transport artifacts`) и byte-stable output при неизменных входах; Verification: idempotent roundtrip test (`gen` дважды без diff).
- [x] 4.4 Добавить/обновить тесты `tests/unit`, `tests/contract`, `tests/integration` по матрице из `artifacts/design/04-testing.md` (positive/negative/regression, drift/check mode); Verification: `uv run pytest tests/unit tests/contract tests/integration`.

## 5. Post-Implementation

- [x] 5.1 После завершения generation implement-фазы актуализировать snapshot и статус Stage B в [docs/roadmap.md](../../../docs/roadmap.md); Verification: consistency review с фактически реализованным объемом `transport-generation`; DoD: roadmap отражает актуальное состояние после генерации без расхождений с OpenSpec change.
