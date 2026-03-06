## 1. Реализация
- [ ] 1.1 Phase: 01; Scope: зафиксировать целевую структуру секций и ключей `.apidev/config.toml`; Output artifact: `artifacts/plan/phase-01.md`; Verification: design-review; DoD: целевая схема согласована и непротиворечива.
- [ ] 1.2 Phase: 01; Scope: подготовить OpenSpec delta для нового конфигурационного capability; Output artifact: `specs/config/spec.md`; Verification: `openspec validate 014-config-refactor --strict --no-interactive`; DoD: delta проходит strict validate.
- [ ] 1.3 Phase: 01; Scope: синхронизировать кросс-capability контракт для release state (`evolution.release_state_file`) между `config` и `contract-evolution-integration`; Output artifact: `specs/contract-evolution-integration/spec.md`; Verification: `openspec validate 014-config-refactor --strict --no-interactive`; DoD: отсутствуют скрытые предпосылки и конфликтующие формулировки.
- [ ] 1.4 Phase: 02; Scope: обновить модель конфигурации и загрузчик под новый контракт без legacy-веток; Output artifact: `src/apidev/core/models/config.py`, `src/apidev/infrastructure/config/toml_loader.py`; Verification: `uv run pytest tests/unit -k "config or loader"`; DoD: loader принимает только новый формат и выдаёт детерминированные ошибки.
- [ ] 1.5 Phase: 02; Scope: обновить `apidev init` и default-config materialization; Output artifact: `src/apidev/commands/init_cmd.py`; Verification: `uv run pytest tests/integration -k "init and config"`; DoD: init создаёт только новый формат.
- [ ] 1.6 Phase: 02; Scope: реализовать path resolution контракт (resolve относительно `project_dir`, normalize before boundary-check, fail-fast при выходе за пределы, детерминированные diagnostics поля); Output artifact: `src/apidev/infrastructure/config/toml_loader.py`, `tests/unit/**`; Verification: `uv run pytest tests/unit -k "config and path"`; DoD: сценарии path validation детерминированы.
- [ ] 1.7 Phase: 03; Scope: добавить регрессионные тесты fail-fast unknown sections/keys с детерминированным `key_path`; Output artifact: `tests/unit/**`, `tests/integration/**`; Verification: `uv run pytest tests/unit -k "unknown key"`, `uv run pytest tests/integration -k "config"`; DoD: неизвестные секции/ключи всегда блокируют выполнение команд.
- [ ] 1.8 Phase: 03; Scope: добавить end-to-end регрессию для `validate`, `diff`, `gen`, `init` под новым контрактом `evolution.release_state_file`; Output artifact: `tests/integration/**`; Verification: `uv run pytest tests/integration -k "validate or diff or gen or init"`; DoD: все 4 команды используют единый resolved config snapshot и корректный release state override.
- [ ] 1.9 Phase: 03; Scope: синхронизировать тесты и документацию; Output artifact: `tests/**`, `docs/**`; Verification: `uv run pytest`, `uv run ruff check src tests`, `uv run mypy src`; DoD: тесты green, docs отражают новый контракт.
- [ ] 1.10 Phase: 03; Scope: финальная валидация OpenSpec-пакета; Output artifact: `artifacts/plan/implementation-handoff.md`; Verification: `openspec validate 014-config-refactor --strict --no-interactive`; DoD: change ready for `/openspec-implement`.

## 2. Плановые ссылки
- `artifacts/plan/phase-01.md`
- `artifacts/plan/phase-02.md`
- `artifacts/plan/phase-03.md`
- `artifacts/plan/implementation-handoff.md`
