# 03. Decisions

## D1. Centralized Compatibility Taxonomy
- Решение: ввести единый taxonomy-модуль классификации совместимости и использовать его как source of truth для `diff` и `gen --check`.
- Причина: требуется консистентный результат для governance режимов и CI.
- Альтернатива: раздельная классификация по командам.
- Почему отклонено: риск расхождения semantics и дрейфа поведения между командами.

## D2. Optional Read-only DBSpec Adapter
- Решение: интеграцию с `dbspec` ограничить read-only адаптером с graceful fallback.
- Причина: `docs/product/vision.md` фиксирует optional nature интеграции.
- Альтернатива: сделать `dbspec` обязательной зависимостью для совместимости.
- Почему отклонено: ломает standalone workflow и усложняет onboarding.

## D3. Explicit Deprecation Lifecycle
- Решение: ввести формальный lifecycle (`active`, `deprecated`, `removed`) и минимальный grace window перед удалением.
- Причина: нужен управляемый переход без неожиданного breaking поведения.
- Альтернатива: разрешить immediate remove по факту изменения контракта.
- Почему отклонено: не дает предсказуемой миграции для потребителей API.

## D4. Deterministic Merge and Reporting
- Решение: нормализовать внешние hints и объединять их с контрактом по стабильной policy с приоритетом contract fields.
- Причина: сохранение детерминированности generation/diff output.
- Альтернатива: best-effort merge без явного порядка приоритетов.
- Почему отклонено: может приводить к нестабильному output и ложному drift.

## D5. Canonical Config and Release-State Source of Truth
- Решение: использовать `.apidev/config.toml` как каноничный конфигурационный источник и хранить release state в `.apidev/release-state.json` по умолчанию (с override через `evolution.release_state_file`).
- Причина: устранение неоднозначности config path и скрытых зависимостей release governance.
- Альтернатива: поддерживать несколько неканоничных путей конфигурации без явной иерархии.
- Почему отклонено: увеличивает риск несовместимого поведения и операционных ошибок.

## D6. Explicit Default for Deprecation Window
- Решение: установить default `grace_period_releases = 2`.
- Причина: требования становятся тестируемыми и одинаково интерпретируются в CI и локальном запуске.
- Альтернатива: оставлять default только как "documented value" без фиксированного числа.
- Почему отклонено: не дает верифицируемого контракта и приводит к неоднозначным реализациям.

## D7. Structured Release Tracking Format
- Решение: фиксировать релизное состояние в `.apidev/release-state.json` как валидируемый JSON-объект (`release_number` и `baseline_ref` mandatory; `released_at`, `git_commit`, `tag` optional).
- Причина: нужен однозначный, машинно-проверяемый формат для deprecation-window checks.
- Альтернатива: хранить релизную информацию в свободном текстовом формате или только через внешние переменные среды.
- Почему отклонено: возрастает риск неоднозначной интерпретации и нестабильности проверок.

## D8. Baseline Snapshot as Mandatory Comparison Source
- Решение: определять compatibility classification только через сравнение текущей нормализованной модели с baseline snapshot, резолвленным по `baseline_ref` (git tag/sha).
- Причина: без исторического baseline невозможно формально определить breaking/non-breaking относительно предыдущего релиза; baseline должен быть одинаково доступен на разных машинах.
- Альтернатива: классифицировать изменения только по текущему состоянию без сохраненной истории.
- Почему отклонено: логически не позволяет доказать breaking change и порождает ложные/недетерминированные выводы.

## D9. Explicit Handling of Missing/Invalid Baseline
- Решение: ввести явные diagnostics `baseline-missing` и `baseline-invalid`; в `strict` policy завершать команду с non-zero exit code.
- Причина: отсутствие baseline должно быть наблюдаемым и управляемым событием, а не скрытой деградацией качества проверки.
- Альтернатива: молча пропускать classification при отсутствии baseline.
- Почему отклонено: маскирует риски несовместимых изменений и ослабляет governance в CI.

## D10. VCS/CI as Authoritative Baseline Source
- Решение: считать VCS/CI-резолв `baseline_ref` каноничным источником baseline; локальные snapshots использовать только как cache-оптимизацию.
- Причина: локальная файловая история может быть потеряна, а командная reproducibility должна сохраняться.
- Альтернатива: полагаться только на `.apidev/releases/*` в рабочей директории.
- Почему отклонено: хрупко при удалении папок, смене компьютера и работе нескольких разработчиков.
