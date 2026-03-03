# Архитектура: Release Automation for Multi-OS Binary Delivery

## Контекст
`apidev` должен получить репозиторный release pipeline для публикации standalone binary под `macOS`, `Windows`, `Linux` с обязательными quality gates и управляемым optional Homebrew path.

## Scope архитектуры
- Входит: GitHub Actions workflow, matrix build/smoke/package, release asset upload, optional Homebrew publish.
- Не входит: изменение runtime-логики CLI команд и доменной бизнес-логики.

## C4 Level 1: System Context
```mermaid
C4Context
title APIDev Release Automation (L1)
Person(maintainer, "Maintainer", "Создает GitHub Release и контролирует публикацию")
Person(dev, "Developer", "Использует опубликованные binary артефакты")
System(apidev_repo, "APIDev Repository", "Source + release workflow + docs/process")
System_Ext(gha, "GitHub Actions", "CI/CD orchestration")
System_Ext(ghr, "GitHub Releases", "Хранение release assets")
System_Ext(tap, "Homebrew Tap Repository", "Формула и артефактный source для brew install")

Rel(maintainer, apidev_repo, "Creates tag/release, dispatches manual release")
Rel(apidev_repo, gha, "Triggers release workflow")
Rel(gha, ghr, "Publishes release assets")
Rel(gha, tap, "Optionally updates formula (secret-gated)")
Rel(dev, ghr, "Downloads standalone binaries")
Rel(dev, tap, "Installs via brew (optional)")
```

## C4 Level 2: Container
```mermaid
C4Container
title APIDev Release Automation Containers (L2)
Person(maintainer, "Maintainer")
System_Boundary(apidev_boundary, "APIDev Release System") {
  Container(repo, "Repository", "Git + docs", "Исходный код, release docs, process checklist")
  Container(workflow, "Release Workflow", "GitHub Actions YAML", "Trigger routing, matrix orchestration, publish sequence")
  Container(build_stage, "Build/Smoke/Package Stages", "Actions jobs", "Сборка бинарника, smoke-check, упаковка артефакта")
  Container(homebrew_stage, "Homebrew Publish Stage (optional)", "Actions job", "Обновление formula в tap-репозитории")
}
System_Ext(ghr, "GitHub Releases", "Release assets and metadata")
System_Ext(artifacts, "Workflow Artifacts", "Промежуточные/отладочные пакеты")
System_Ext(tap, "Homebrew Tap Repo", "Formula updates")
System_Ext(secrets, "GitHub Secrets", "HOMEBREW_TAP_TOKEN")

Rel(maintainer, repo, "Publishes release/tag")
Rel(repo, workflow, "Provides workflow definitions")
Rel(workflow, build_stage, "Starts matrix jobs per OS/arch")
Rel(build_stage, artifacts, "Uploads packaged artifacts")
Rel(build_stage, ghr, "Publishes final release assets")
Rel(workflow, homebrew_stage, "Runs optional gated path")
Rel(homebrew_stage, secrets, "Requires tap token")
Rel(homebrew_stage, tap, "Pushes formula update")
```

## C4 Level 3: Component
```mermaid
C4Component
title Release Workflow Components (L3)
Container_Boundary(release_workflow, "Release Workflow") {
  Component(trigger_router, "Trigger Router", "workflow events", "Нормализует release:published и workflow_dispatch в единый run-context")
  Component(matrix_planner, "Matrix Planner", "job strategy", "Определяет OS/arch матрицу и naming inputs")
  Component(binary_builder, "Binary Builder", "build step", "Собирает standalone binary для целевой платформы")
  Component(smoke_gate, "Smoke Gate", "validation step", "Проверяет запуск apidev --help и блокирует publish при ошибке")
  Component(packager, "Artifact Packager", "archive step", "Формирует детерминированные архивы по naming contract")
  Component(release_publisher, "Release Publisher", "upload step", "Загружает assets в GitHub Release и workflow artifacts")
  Component(homebrew_guard, "Homebrew Guard", "pre-check step", "Проверяет наличие/валидность секрета для publish path")
  Component(homebrew_publisher, "Homebrew Publisher", "publish step", "Обновляет formula в tap-репозитории")
}
Rel(trigger_router, matrix_planner, "Builds execution context")
Rel(matrix_planner, binary_builder, "Fan-out by matrix target")
Rel(binary_builder, smoke_gate, "Passes built binary")
Rel(smoke_gate, packager, "Allows packaging on success")
Rel(packager, release_publisher, "Passes deterministic artifact bundles")
Rel(homebrew_guard, homebrew_publisher, "Enables publish if token is valid")
Rel(release_publisher, homebrew_guard, "Provides release metadata/version")
```

## Архитектурные инварианты
- Публикация release assets запрещена при провале smoke-check в любой обязательной ветке матрицы.
- Именование артефактов должно быть детерминированным и воспроизводимым из version + target (`os`, `arch`).
- Optional Homebrew path изолирован от базового multi-OS publish и не должен создавать partial release assets.
- Документация Distribution/Release process должна отражать фактический pipeline contract.

## Assumptions
- GitHub Releases является единственным source of truth для binary дистрибуции первой итерации.
- Сборка standalone binary для `apidev` реализуема в CI без внешней ручной сборки.
- Runner matrix `macOS|Windows|Linux` покрывает целевую аудиторию текущего этапа Horizon 2.

## Risks
- Различия toolchain/packaging между ОС могут вызвать platform-specific flaky failures.
- Длительность matrix pipeline может увеличиться и снизить throughput release-процесса.
- Ошибки в naming/version extraction способны привести к mismatch между тегом и asset именами.

## Open Questions
- Нужна ли поддержка нескольких архитектур (`amd64` + `arm64`) во всех ОС в первой итерации?
- Нужна ли автоматическая подпись/checksum verification как обязательный gate первой итерации?

## Resolved Decisions for Implement
- `workflow_dispatch` MUST принимать явный `release_version` input; pipeline SHALL падать при отсутствии/пустом значении, чтобы исключить недетерминированный version source.
- Homebrew publish path фиксируется как isolated non-blocking path относительно core assets: при pre-check failure job завершаетcя controlled failure и не откатывает уже консистентно опубликованные GitHub Release assets.
