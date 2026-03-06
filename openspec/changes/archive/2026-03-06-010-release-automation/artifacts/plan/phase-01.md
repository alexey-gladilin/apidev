# Phase 01: Release Workflow Skeleton and Multi-OS Core

## Цель
Собрать минимально полный и проверяемый release workflow-контур для multi-OS публикации бинарников `apidev`.

## Зависимости фазы
- Входы: `proposal.md`, `design.md`, `artifacts/design/01-architecture.md`, `artifacts/design/02-behavior.md`, `specs/release-automation/spec.md`.
- Блокирующие зависимости: отсутствуют (стартовая implement-фаза).
- Выходы фазы являются входом для `Phase 02`.

## Scope
- Добавить baseline GitHub release workflow с trigger `release: published` и `workflow_dispatch`.
- Реализовать matrix build/smoke/package path для `macOS|Windows|Linux`.
- Зафиксировать deterministic artifact naming/version wiring и публикацию в workflow artifacts + GitHub Release assets.

## Output Artifacts
- `.github/workflows/release*.yml`
- `scripts/release/*` (если требуется для build/smoke/package)
- `Makefile` (если требуется унификация CI-команд)

## Verification
- `actionlint .github/workflows/release*.yml`
- тестовый запуск workflow на `workflow_dispatch` с проверкой matrix веток
- проверка smoke gate (`apidev --help`) до шага публикации

## Definition of Done
- Workflow детерминированно запускается на `release: published` и `workflow_dispatch`.
- Для всех обязательных targets (`macOS|Windows|Linux`) build/smoke/package проходят в консистентной последовательности.
- Release assets используют схему `apidev-<version>-<os>-<arch>` и не публикуются при провале обязательного gate.

## Риски
- Платформенные различия toolchain могут вызвать нестабильность matrix-сборки.
- Неверная маршрутизация version context может привести к неправильным именам артефактов.
- Параллельный publish без строгого gate может дать partial release.

## Rollback Notes
- При критическом сбое откатить новый release workflow до последней стабильной ревизии через revert PR.
- Временно отключить автоматический trigger `release: published`, оставив только ручной прогон для диагностики.
- При naming mismatch заблокировать publish step до исправления mapping версии/платформ.
