# Rule Update Record: AR-006 в `012-integration`

## Статус
`Reference`

## Назначение
Документ фиксирует, какое изменение архитектурного правила было принято в рамках `012-integration`, и где это изменение отражено в repository-wide документации.

## Актуальное правило для `012-integration`
- Запись generated/scaffold-артефактов разрешена в пределах `project_dir`.
- `generator.generated_dir` и `generator.scaffold_dir` — независимые контуры.
- Оба контура обязаны проходить единый path-boundary контроль.
- Любой выход за границы `project_dir` должен завершаться fail-fast диагностикой.

## Где зафиксировано актуальное правило
- `docs/architecture/architecture-rules.md` (AR-006)
- `docs/architecture/architecture-overview.md`
- `docs/architecture/validation-blueprint.md`
- `docs/architecture/generated-integration.md`
- `openspec/changes/012-integration/specs/cli-tool-architecture/spec.md`

## Правило для implement-review
- В реализации и review не допускается расхождение между `docs/architecture/*` и OpenSpec-артефактами `012-integration`.
- Security/boundary проверки остаются обязательными: fail-fast и единый path-boundary policy внутри `project_dir`.
