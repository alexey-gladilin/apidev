## 1. Спецификация формата
- [x] 1.1 Согласовать canonical contract shape для shared model files, `$ref`, shorthand `$...` refs и operation-local models.
- [x] 1.2 Зафиксировать список допустимых мест использования ссылок: property node, `items.ref`, при наличии поддержки `values.ref` и аналогичных составных узлов.
- [x] 1.3 Описать semantic boundary между shared models и operation-local models с позитивными и негативными примерами.
- [x] 1.4 Зафиксировать directory layout и правила различения `operation contract` vs `shared model contract` для аналитиков, разработчиков и tooling.

## 2. Подготовка `apidev`
- [x] 2.1 Обновить `docs/reference/contract-format.md`, добавив второй canonical YAML contract kind для shared models и их расположение.
- [ ] 2.2 Подготовить migration guide для аналитиков и backend-команд по выносу типовых reusable моделей.
- [ ] 2.3 Подготовить и согласовать обновление `apidev/docs/reference/contract-format.md` с примерами `before/after`.

## 3. Фаза реализации кода (`apidev`)
- [ ] 3.1 Обновить Pydantic contract models и loader для поддержки shared model files и `ref`.
- [ ] 3.2 Добавить поддержку `contracts.shared_models_dir` с дефолтом `.apidev/models`.
- [ ] 3.3 Добавить semantic validation: missing ref, scope leak, wrong directory/contract_type mismatch, duplicate names, cycle policy, ambiguous resolution.
- [ ] 3.4 Реализовать normalized model registry и детерминированное разрешение short-name/fully-qualified refs без специальных правил для namespace `common`.
- [ ] 3.5 Реализовать graph-aware validation в `apidev validate`, включая cycle detection и machine-readable cycle diagnostics.
- [ ] 3.6 Добавить CLI-команду introspection dependency graph с поддержкой как минимум `text`, `json` и `mermaid` output.

## 4. Верификация
- [ ] 4.1 Добавить contract tests на успешные сценарии shared refs.
- [ ] 4.2 Добавить negative tests на `missing ref`, `scope leak`, `cycle` (включая self-reference), `name collision`/`ambiguous short-name`, `wrong location`, `contract_type mismatch`.
- [ ] 4.3 Добавить tests на graph CLI: direct deps, reverse deps, JSON output shape и Mermaid export.
- [ ] 4.4 Подтвердить backward-compatible mixed mode для inline-only контрактов.

## 5. Валидация change
- [ ] 5.1 Выполнить `openspec validate 014-shared-contract-models --strict --no-interactive` и устранить замечания.
