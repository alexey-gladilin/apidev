# Testing Strategy: Release Automation

## Цели проверки
- Доказать запуск и корректную маршрутизацию release pipeline по `release: published` и `workflow_dispatch`.
- Доказать прохождение multi-OS build/smoke/package этапов перед публикацией assets.
- Доказать детерминированный artifact naming contract.
- Доказать controlled behavior optional Homebrew path при валидном/невалидном секрете.
- Доказать синхронизацию process docs с фактическими quality gates.

## Test layers

## 1. Workflow-level validation
- Проверка синтаксиса и структуры workflow-файла (`actionlint`/эквивалент).
- Проверка наличия обязательных triggers и matrix targets (`macOS`, `Windows`, `Linux`).
- Проверка зависимостей job order: build -> smoke -> package -> publish.

## 2. Integration checks в CI run
- Smoke verification per target: запуск `apidev --help` на каждом matrix runner.
- Проверка упаковки артефактов и наличия expected filenames по шаблону `apidev-<version>-<os>-<arch>`.
- Проверка, что release upload stage не выполняется при failure в build/smoke/package.

## 3. Release contract checks
- Проверка, что успешный run публикует assets в GitHub Release.
- Проверка, что workflow artifacts соответствуют release inventory.
- Проверка отсутствия partial/несогласованной публикации при fail-path.

## 4. Homebrew path checks (optional)
- Positive path: валидный секрет -> formula update job проходит.
- Negative path: отсутствующий/невалидный секрет -> controlled failure без partial publish.
- Проверка изоляции: failure Homebrew path не должен ломать уже консистентно опубликованные core assets.

## 5. Process/documentation checks
- Проверка наличия раздела Distribution в `README.md`.
- Проверка наличия и актуальности release checklist в `docs/process/*`.
- Проверка трассируемости checklist шагов к job/command quality gates.

## Scenario-to-Test traceability
- Spec Scenario: `Release trigger starts multi-OS build`
  - Tests: trigger routing + matrix presence + manual dispatch parity.
- Spec Scenario: `Binary smoke checks gate artifact publication`
  - Tests: smoke per target + publish blocked on smoke fail.
- Spec Scenario: `Release assets are published deterministically`
  - Tests: filename pattern checks + release assets inventory consistency.
- Spec Scenario: `Distribution surface is documented`
  - Tests: README Distribution section existence and completeness review.
- Spec Scenario: `Release checklist is explicit and test-backed`
  - Tests: docs/process checklist and linkage to CI jobs.
- Spec Scenario: `Homebrew publish is secret-gated`
  - Tests: secret pre-check success/fail behavior.

## Quality gates
- `openspec validate 010-release-automation --strict --no-interactive`
- CI workflow lint/check (например, `actionlint`).
- Integration run на test release или controlled dry-run environment.
- Ручной review process docs на согласованность с фактическим pipeline.

## Assumptions
- В CI доступен механизм запуска тестового release или эквивалентного dry-run.
- Набор runner-образов GitHub Actions стабилен и покрывает нужные платформенные зависимости.

## Risks
- Часть release-проверок зависит от внешнего GitHub окружения и может быть нестабильной в fork/sandbox.
- Недостаточный negative-path coverage может скрыть partial publish edge-cases.

## Open Questions
- Нужен ли локальный эмулятор release pipeline для pre-merge проверок без фактического релиза?
- Следует ли добавить обязательную checksum verification в quality gates текущего change?
