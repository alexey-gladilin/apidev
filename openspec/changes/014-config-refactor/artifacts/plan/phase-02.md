# Phase 02 — Модель и загрузчик

## Scope
- Обновить `config` model под новый контракт.
- Обновить TOML loader и path validation под строгую fail-fast модель.
- Синхронизировать `init` materialization.

## Outputs
- `src/apidev/core/models/config.py`
- `src/apidev/infrastructure/config/toml_loader.py`
- `src/apidev/commands/init_cmd.py`

## Verification
- `uv run pytest tests/unit -k "config or loader"`
- `uv run pytest tests/integration -k "init and config"`
