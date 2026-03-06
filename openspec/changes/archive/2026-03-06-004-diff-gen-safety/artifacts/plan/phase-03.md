# Phase 03 — Verification Matrix, CLI Contract Sync & Readiness

## Цель
Собрать верификационный контур implement-фазы и подготовить финальный handoff без planning-блокеров.

## Планируемые шаги
1. Сформировать матрицу unit/contract/integration сценариев для `REQ-1..REQ-4`.
2. Уточнить обязательные negative safety сценарии: validation failure, boundary violation, non-mutation proof.
3. Синхронизировать CLI contract (`diff`, `gen --check`, `gen`) и команды верификации для CI readiness.
4. Подготовить финальный implementation handoff с зависимостями фаз.

## Выходы
- Тестовая матрица и quality gates: `artifacts/design/04-testing.md`
- Финальный handoff-документ: `artifacts/plan/implementation-handoff.md`
- Обновленный planning tracker: `tasks.md`

## Quality Gate
- Каждое требование spec delta связано минимум с одним автотест-сценарием.
- Определен минимальный CI-набор команд и критерии прохождения.
- Change-пакет готов к запуску `/openspec-implement` без открытых planning-вопросов.
