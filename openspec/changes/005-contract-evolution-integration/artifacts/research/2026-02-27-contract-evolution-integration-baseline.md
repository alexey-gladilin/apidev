# Research Baseline: Contract Evolution & Integrations (2026-02-27)

## Scope
- Зафиксировать фактическое состояние репозитория для этапа D (`compatibility classification`, `optional dbspec integration`, `formal deprecation policy`).
- Сформировать evidence-only baseline без реализации и без продуктовых рекомендаций.

## Evidence
1. `docs/roadmap.md`
- Этап D определен как `Contract Evolution & Integrations`.
- Явно перечислены три целевых направления: `compatibility classification`, `optional dbspec integration`, `formal deprecation policy`.

2. `src/apidev/core/rules/compatibility.py`
- Файл содержит placeholder (`# Placeholder for future backward-compatibility checks.`).
- Нормативные compatibility rules в коде на дату снимка отсутствуют.

3. `src/apidev/application/services/diff_service.py`
- Сервис строит generation plan и deterministic fingerprint для contract payload.
- Явная классификация изменений по категориям совместимости в текущем поведении отсутствует.

4. `src/apidev/commands/diff_cmd.py` и `src/apidev/commands/generate_cmd.py`
- Команды обеспечивают текущие сценарии diff/generate/check.
- Политики fail-on-breaking и deprecation-specific output в CLI-контрактах не зафиксированы.

5. `docs/product/vision.md`
- Зафиксировано, что интеграция с `dbspec` рассматривается как опциональная и read-only.
- Базовый workflow APIDev должен оставаться работоспособным без обязательной связки с `dbspec`.

6. `docs/reference/cli-contract.md` и `docs/reference/contract-format.md`
- В документации есть текущий CLI/contract baseline (validate/diff/gen), но формализованной deprecation policy и compatibility taxonomy для этапа D нет.

7. `tests/`
- Присутствуют unit/contract/integration тесты на deterministic generation, validate/diff behavior и архитектурные инварианты.
- Специфические тест-кейсы для compatibility classification и deprecation lifecycle на дату снимка не обнаружены.

## Baseline Conclusions
- Этап D на дату снимка (27 февраля 2026) не реализован как формальный capability-пакет.
- В кодовой базе есть инфраструктурные точки расширения (rules/services/commands/tests), пригодные для implement-фазы.
- На уровне roadmap/vision уже зафиксированы boundaries: `dbspec` integration optional + read-only.

## Files reviewed
- `docs/roadmap.md`
- `docs/product/vision.md`
- `docs/reference/cli-contract.md`
- `docs/reference/contract-format.md`
- `src/apidev/core/rules/compatibility.py`
- `src/apidev/application/services/diff_service.py`
- `src/apidev/commands/diff_cmd.py`
- `src/apidev/commands/generate_cmd.py`
- `tests/unit/**`, `tests/contract/**`, `tests/integration/**`
