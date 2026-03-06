# Тестирование: Transport Generation MVP+

## 1. Цели тестирования
- Подтвердить deterministic output для registry/router/models/errors.
- Подтвердить runnable transport wiring и корректный bridge contract.
- Подтвердить сохранение generated/manual boundary при `gen` и `gen --check`.

## 2. Матрица проверок
- Unit: рендеринг template-контекста для registry, router, request/response/error моделей.
- Unit: deterministic ordering operation registry при одинаковом входе.
- Contract: write-boundary и отсутствие изменений вне generated root.
- Contract: bridge signature contract и стабильность operation metadata.
- Integration: end-to-end `init -> validate -> gen` с проверкой runnable skeleton.
- Integration: `gen --check` для drift detection на измененных и неизмененных входах.

## 3. Минимальные команды в implement-фазе
- `uv run pytest tests/unit -k "generate or diff"`
- `uv run pytest tests/contract/architecture`
- `uv run pytest tests/integration/test_generate_roundtrip.py`

## 4. Definition of Done для тестов
- Все обязательные сценарии из spec delta имеют покрытие.
- Regression-набор фиксирует byte-stable generation на неизмененных контрактах.
- Нет регрессий по write-boundary policy.
- Проверки проходят в локальном CI-пайплайне без flaky поведения.
