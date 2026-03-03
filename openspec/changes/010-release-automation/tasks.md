## 1. Phase 01 - Release Workflow Skeleton and Multi-OS Core ([plan](./artifacts/plan/phase-01.md))
Зависимости фазы: стартовая фаза (без блокирующих зависимостей), выходы обязательны для Phase 02.
Статус контекста: фаза уже реализована и зафиксирована в репозитории; используется как закрытая зависимость для текущего implement-цикла.

- [x] 1.1 Phase: 01; Scope: добавить baseline GitHub release workflow с multi-OS matrix (`macOS|Windows|Linux`) и trigger `release: published|workflow_dispatch`; Output artifact: `.github/workflows/release*.yml`; Verification: `actionlint .github/workflows/release*.yml` + dry-run на `workflow_dispatch`; DoD: workflow детерминированно запускается и покрывает все целевые ОС.
- [x] 1.2 Phase: 01; Scope: внедрить build/smoke/package шаги для standalone binary `apidev` в каждой ОС; Output artifact: `scripts/release/*`, `Makefile`, `.github/workflows/release*.yml`; Verification: smoke gate `apidev --help` в matrix run; DoD: бинарники собираются и проходят smoke-check до публикации.
- [x] 1.3 Phase: 01; Scope: закрепить deterministic artifact naming/version wiring и upload в workflow artifacts + GitHub Release assets; Output artifact: `.github/workflows/release*.yml`; Verification: проверка naming inventory в CI run; DoD: схема `apidev-<version>-<os>-<arch>` выполняется для всех обязательных target платформ.

## 2. Phase 02 - Release Publishing Surface and Homebrew Path ([plan](./artifacts/plan/phase-02.md))
Зависимости фазы: требуется завершение Phase 01 и стабильный workflow contract.

- [ ] 2.1 Phase: 02; Scope: добавить release process/checklist docs с обязательными quality gates; Output artifact: `docs/process/release*.md`; Verification: `make docs-check`; DoD: maintainer может выполнить release без неявных шагов.
- [ ] 2.2 Phase: 02; Scope: обновить `README.md` секцией Distribution (GitHub Releases install path, binary assets); Output artifact: `README.md`; Verification: docs review + link checks; DoD: пользователю доступен понятный путь получения бинарника.
- [ ] 2.3 Phase: 02; Scope: добавить optional Homebrew publish path как отдельную gated job (secret-required); Output artifact: `.github/workflows/release*.yml`, `scripts/release/*`; Verification: positive/negative path checks для секрета; DoD: publish path безопасно блокируется при отсутствии/невалидности секрета и не нарушает core assets.
- [ ] 2.4 Phase: 02; Scope: зафиксировать explicit version-source contract для `workflow_dispatch` через обязательный input `release_version` и fail-fast pre-check; Output artifact: `.github/workflows/release*.yml`, `docs/process/release*.md`; Verification: negative path (missing/empty input) + deterministic naming checks; DoD: ручной запуск не может публиковать артефакты с невалидным version context.

## 3. Phase 03 - Reliability, Governance, and Validation Readiness ([plan](./artifacts/plan/phase-03.md))
Зависимости фазы: требуется завершение Phase 01-02 и синхронизация workflow+docs.

- [ ] 3.1 Phase: 03; Scope: ввести regression tests/guards для release workflow contract и release docs синхронизации; Output artifact: `tests/**`, `docs/process/release*.md`; Verification: `make test`, `make docs-check`; DoD: release contract не деградирует без явного изменения тестов/документации.
- [ ] 3.2 Phase: 03; Scope: зафиксировать security/reproducibility требования release pipeline (supply-chain, pinning, permissions); Output artifact: `.github/workflows/release*.yml`, `docs/process/release*.md`; Verification: security review checklist; DoD: release pipeline соответствует внутренним security guardrails.
- [ ] 3.3 Phase: 03; Scope: пройти strict OpenSpec validation change-пакета перед implement; Output artifact: `openspec validate 010-release-automation --strict --no-interactive`; Verification: strict validation pass; DoD: пакет готов к отдельной implement-фазе.
