# Phase 03: Reliability, Governance, and Validation Readiness

## Цель
Зафиксировать устойчивость release contract через regression guards, security/reproducibility правила и strict OpenSpec readiness.

## Зависимости фазы
- Входы: артефакты `Phase 01` и `Phase 02`, `artifacts/design/04-testing.md`, `specs/release-automation/spec.md`.
- Блокирующие зависимости: реализованный workflow + документация release surface.
- Фаза завершает plan-to-implement контур.

## Scope
- Добавить regression checks для release workflow contract и синхронизации документации.
- Зафиксировать security/reproducibility guardrails (pinning, permissions, supply-chain ограничения).
- Пройти strict OpenSpec validation и подтвердить implement readiness.

## Output Artifacts
- `tests/**` (контрактные/regression проверки release pipeline)
- `.github/workflows/release*.yml` (hardening/pinning/permissions)
- `docs/process/release*.md` и связанные reference docs
- отчет strict validation для change `010-release-automation`

## Verification
- `uv run pytest tests/unit tests/integration -k "release or workflow or docs"` (или эквивалентный таргет проекта)
- `make docs-check`
- `openspec validate 010-release-automation --strict --no-interactive`

## Definition of Done
- Release contract защищен regression-проверками и не деградирует без явного изменения тестов/спеков.
- Security/reproducibility требования отражены в workflow и docs и проходят review-checklist.
- Change-пакет проходит strict validation и готов к отдельной implement-фазе.

## Риски
- Неполный negative-path coverage может пропустить partial publish edge-cases.
- Чрезмерно строгие guardrails могут ухудшить операционную скорость релизов.
- Разрыв между тестовыми dry-run и фактическим GitHub release окружением может скрывать реальные сбои.

## Rollback Notes
- При падениях из-за hardening-изменений откатить только security/pinning слой, сохранив рабочий core publish.
- При нестабильных regression checks временно перевести их в non-blocking режим до устранения flaky причин.
- Если strict validation блокируется форматом документов, зафиксировать минимальный корректный набор и повторить валидацию отдельным PR.
