# Research: Baseline для Horizon 2 (Release Automation)

Дата: 2026-03-02  
Статус: Approved (fact-only)

## Summary
`dbspec` уже имеет рабочий GitHub release-поток для бинарников под `macOS/Windows/Linux` (build, smoke-test, packaging, release assets, Homebrew publish).  
На срезе baseline для `apidev` отсутствовали полный release/distribution surface в `README` и процессный release checklist; `docs/roadmap.md` фиксирует Horizon 2 как текущий продуктовый фокус.

## Findings (facts only)
- В `dbspec` workflow запускается на `release: published` и `workflow_dispatch`.
- В `dbspec` используется matrix build для `ubuntu-latest`, `windows-latest`, `macos-latest`.
- В `dbspec` присутствуют шаги build + smoke test для onefile, плюс macOS onedir поток для Homebrew.
- В `dbspec` артефакты пакуются и загружаются как workflow artifacts и как GitHub Release assets.
- В `dbspec` есть отдельная `publish-homebrew` job с проверкой `HOMEBREW_TAP_TOKEN` и push formula в tap-репозиторий.
- В `dbspec` README документирует публикацию standalone binaries в GitHub Releases и установку через Homebrew.
- В `apidev` baseline-срез не покрывал полный production release contract (документация процесса, Distribution section, governance/security guardrails).
- В `apidev` roadmap выделяет `Horizon 2 — Release Automation` как отдельный рабочий горизонт.

## Code references
- `/Users/alex/1.PROJECTS/Personal/devtools/dbspec/.github/workflows/release-binaries.yml:4`
- `/Users/alex/1.PROJECTS/Personal/devtools/dbspec/.github/workflows/release-binaries.yml:21`
- `/Users/alex/1.PROJECTS/Personal/devtools/dbspec/.github/workflows/release-binaries.yml:48`
- `/Users/alex/1.PROJECTS/Personal/devtools/dbspec/.github/workflows/release-binaries.yml:64`
- `/Users/alex/1.PROJECTS/Personal/devtools/dbspec/.github/workflows/release-binaries.yml:121`
- `/Users/alex/1.PROJECTS/Personal/devtools/dbspec/.github/workflows/release-binaries.yml:127`
- `/Users/alex/1.PROJECTS/Personal/devtools/dbspec/README.md:119`
- `/Users/alex/1.PROJECTS/Personal/devtools/dbspec/README.md:121`
- `/Users/alex/1.PROJECTS/Personal/devtools/dbspec/README.md:123`
- `/Users/alex/1.PROJECTS/Personal/devtools/apidev/README.md:1`
- `/Users/alex/1.PROJECTS/Personal/devtools/apidev/docs/roadmap.md:59`
- `/Users/alex/1.PROJECTS/Personal/devtools/apidev/Makefile:5`

## Open questions
- Является ли публикация Homebrew для `apidev` обязательной частью первой итерации Horizon 2 или может идти отдельной фазой?
- Есть ли внешний release-процесс для `apidev`, не отраженный в этом репозитории?

## Fact / Inference
- Fact:
  - `dbspec` содержит реализованный multi-OS GitHub release workflow для бинарников и Homebrew publish.
  - baseline `apidev` имел неполный release contract относительно целевого Horizon 2.
  - `apidev` roadmap явно фиксирует необходимость Release Automation.
- Inference:
  - Для достижения цели Horizon 2 в `apidev` необходим репозиторный CI/CD слой на уровне release workflow + release docs/process.
