# Implementation Handoff: 011-cmd-gen-additional-args

## Что реализовать
1. Добавить аргументы `--include-endpoint` и `--exclude-endpoint` в `apidev gen`.
2. Протянуть фильтры в application/service слой.
3. Реализовать deterministic selection endpoint-ов по правилу `include -> exclude`.
4. Добавить diagnostics для invalid pattern и empty effective set.
5. Обновить документацию и тесты.

## Ключевые файлы
- `src/apidev/commands/generate_cmd.py`
- `src/apidev/application/services/generate_service.py`
- `src/apidev/application/services/diff_service.py`
- `docs/reference/cli-contract.md`
- `tests/unit/**`
- `tests/integration/**`

## Критерии приемки
- Новые флаги доступны в help.
- Без флагов поведение обратносуместимо.
- Filtering semantics deterministic и покрыта тестами.
- Strict OpenSpec validation проходит.

## Связи
- Core tasks: [../../tasks.md](../../tasks.md)
- Design summary: [../../design.md](../../design.md)
- Design package: [../design/README.md](../design/README.md)
