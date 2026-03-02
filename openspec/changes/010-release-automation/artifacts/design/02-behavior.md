# Behavior Contract: Release Automation

## Триггеры и входные контексты

### `release: published`
- pipeline стартует автоматически при публикации GitHub Release;
- source версии берется из release/tag metadata;
- запускается полный multi-OS контур (build -> smoke -> package -> publish).

### `workflow_dispatch`
- pipeline поддерживает ручной запуск для контролируемых прогонов;
- ручной запуск должен использовать тот же поведенческий контракт и quality gates, что и автоматический.

## Поведение multi-OS pipeline

### 1. Matrix build
- для каждой целевой платформы (`macOS`, `Windows`, `Linux`) выполняется сборка standalone binary;
- сборка использует единый naming context для версии и target-параметров.

### 2. Smoke gate
- после сборки для каждой платформы выполняется smoke-check `apidev --help`;
- при провале smoke-check конкретная matrix-ветка считается failed;
- публикация release assets не выполняется, если обязательная matrix-ветка failed.

### 3. Packaging
- успешные бинарники упаковываются в детерминированные артефакты;
- naming contract: `apidev-<version>-<os>-<arch>`;
- бинарники публикуются как workflow artifacts для трассировки и повторной диагностики.

### 4. Release publication
- публикация в GitHub Releases выполняется только после прохождения обязательных quality gates;
- набор release assets должен быть консистентным для всех обязательных matrix targets;
- при ошибке публикации процесс завершается fail без silent partial success.

## Поведение optional Homebrew path
- Homebrew path запускается отдельной job и не смешивается с core multi-OS job chain;
- job должна выполнять pre-check секрета (например, `HOMEBREW_TAP_TOKEN`);
- при отсутствии/невалидности секрета job завершаетcя контролируемой ошибкой;
- controlled failure не должна нарушать уже опубликованные GitHub release assets core-пайплайна.

## Документационный контракт
- `README.md` содержит Distribution section с источником артефактов и install-path;
- process docs содержат checklist шагов `version/tag/build/smoke/publish`;
- checklist явно ссылается на команды/джобы, подтверждающие quality gates.

## Failure Semantics
- `build failed` -> target не публикуется, release publish stage блокируется.
- `smoke failed` -> target не публикуется, release publish stage блокируется.
- `package failed` -> release publish stage блокируется.
- `release upload failed` -> pipeline failed, требуется retry/ручное расследование.
- `homebrew pre-check failed` -> Homebrew stage failed controlled way, core artifacts остаются консистентными.

## Assumptions
- Версия релиза однозначно определяется из release/tag контекста.
- Smoke-check `apidev --help` достаточен как минимальный gate работоспособности бинарника на этапе Horizon 2.

## Risks
- Ручной `workflow_dispatch` без строгой валидации входов может приводить к публикации с неверным version context.
- Разные форматы архивов по ОС усложняют post-release поддержку install-инструкций.

## Open Questions
- Нужен ли отдельный pre-release режим (например, RC/nightly) с отличающимся именованием артефактов?
- Нужны ли дополнительные smoke-команды помимо `--help` для критичных платформенных сценариев?
