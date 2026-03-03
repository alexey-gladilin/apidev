# Baseline Research: endpoint include/exclude для `apidev gen`

## Scope
- Вопрос: какие фактические точки расширения уже существуют для CLI-аргументов и generation pipeline, чтобы добавить include/exclude endpoint без изменения контракта YAML.
- In-scope: `generate_cmd`, `GenerateService`, `DiffService`, YAML loader, CLI contract docs.
- Out-of-scope: реализация solution и выбор финального синтаксиса pattern.

## Summary
Текущий `apidev gen` поддерживает несколько override-флагов и делегирует построение плана в `GenerateService -> DiffService`, где операции загружаются полностью из `contracts/**/*.yaml` и сортируются по `operation_id`. Фактической фильтрации endpoint-ов по include/exclude в pipeline сейчас нет.

## Findings (facts only)
1. `apidev gen` уже имеет расширяемую поверхность CLI-аргументов (`--scaffold`, `--no-scaffold`, `--compatibility-policy`, `--baseline-ref`) и передает override-значения в `GenerateService.run(...)`.
   - Evidence: `src/apidev/commands/generate_cmd.py:44-74`, `src/apidev/commands/generate_cmd.py:130-136`.
2. `GenerateService.run(...)` проксирует входные параметры в `DiffService.run(...)`, затем применяет write/remove по рассчитанному плану.
   - Evidence: `src/apidev/application/services/generate_service.py:47-63`, `src/apidev/application/services/generate_service.py:94-125`.
3. `DiffService.run(...)` загружает полный список операций `loader.load(paths.contracts_dir)`, проверяет уникальность `operation_id`, сортирует операции и генерирует artifacts для каждого `op`.
   - Evidence: `src/apidev/application/services/diff_service.py:77-83`, `src/apidev/application/services/diff_service.py:145-173`.
4. Загрузка контрактов основана на проходе по всем `*.yaml` в `contracts_root` (`rglob`) и формировании `operation_id` из относительного пути контракта.
   - Evidence: `src/apidev/infrastructure/contracts/yaml_loader.py:19-22`, `src/apidev/infrastructure/contracts/yaml_loader.py:53-55`.
5. Документированный CLI-контракт сейчас описывает scaffold flags и не содержит endpoint include/exclude флагов.
   - Evidence: `docs/reference/cli-contract.md:45-56`.

## Resolved Questions (for design handoff)
- Фильтрация scope данного change ограничена `apidev gen`; `apidev diff` остается без изменений.
- Нормативный pattern type: case-sensitive glob по `operation_id` и `contract_relpath` (правило matching: `OR`).
- Невалидные pattern: пустая строка и malformed glob syntax (включая незакрытый `[` character-class).

## Fact / Inference
### Fact
- Текущий код не содержит endpoint include/exclude фильтрации на уровне `generate_cmd`/`GenerateService`/`DiffService`.

### Inference
- Наиболее низкорисковая точка для интеграции фильтрации находится между `loader.load(...)` и циклами генерации `for op in enriched_operations`, потому что здесь уже формируется canonical ordered набор операций.
