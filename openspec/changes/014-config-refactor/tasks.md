## 1. Реализация
- [ ] 1.1 Phase: 01; Scope: зафиксировать целевую структуру секций и ключей `.apidev/config.toml`; Output artifact: `artifacts/plan/phase-01.md`; Verification: design-review; DoD: целевая схема согласована и непротиворечива.
- [ ] 1.2 Phase: 01; Scope: подготовить OpenSpec delta для нового конфигурационного capability; Output artifact: `specs/config/spec.md`; Verification: `openspec validate 014-config-refactor --strict --no-interactive`; DoD: delta проходит strict validate.
- [ ] 1.3 Phase: 02; Scope: обновить модель конфигурации и загрузчик под новый контракт без legacy-веток; Output artifact: `src/apidev/core/models/config.py`, `src/apidev/infrastructure/config/toml_loader.py`; Verification: `uv run pytest tests/unit -k "config or loader"`; DoD: loader принимает только новый формат и выдаёт детерминированные ошибки.
- [ ] 1.4 Phase: 02; Scope: обновить `apidev init` и default-config materialization; Output artifact: `src/apidev/commands/init_cmd.py`; Verification: `uv run pytest tests/integration -k "init and config"`; DoD: init создаёт только новый формат.
- [ ] 1.5 Phase: 03; Scope: синхронизировать тесты и документацию; Output artifact: `tests/**`, `docs/**`; Verification: `uv run pytest`, `uv run ruff check src tests`, `uv run mypy src`; DoD: тесты green, docs отражают новый контракт.
- [ ] 1.6 Phase: 03; Scope: финальная валидация OpenSpec-пакета; Output artifact: `artifacts/plan/implementation-handoff.md`; Verification: `openspec validate 014-config-refactor --strict --no-interactive`; DoD: change ready for `/openspec-implement`.

## 2. Плановые ссылки
- `artifacts/plan/phase-01.md`
- `artifacts/plan/phase-02.md`
- `artifacts/plan/phase-03.md`
- `artifacts/plan/implementation-handoff.md`
