# Исследование: gap между operation-first и ожидаемым domain-first layout

Статус: `Research Artifact`
Дата: 1 марта 2026

## Область
Сопоставить:
- текущий фактический output `apidev gen`;
- нормативные/квазинормативные документы репозитория;
- ожидаемую структуру целевого API-проекта с feature/domain-first модулями.

## Наблюдения
1. Входной контрактный слой уже доменный (`<domain>/<operation>.yaml`), а `operation_id` строится из домена + имени файла.
2. Текущий generation output operation-first:
   - `routers/<operation_id>.py`
   - `transport/models/<operation_id>_{request,response,error}.py`
   - плюс `operation_map.py`, `openapi_docs.py`.
3. Тестовые контракты жестко ожидают operation-first пути, следовательно это закрепленное текущее поведение.
4. В research baseline внешнего API-проекта зафиксирован feature/domain-first паттерн (`<domain>/routes.py`, `<domain>/schemas.py`, ...), который лучше совпадает с архитектурой целевых приложений.

## Вывод
Наблюдается структурный gap: вход организован по доменам, выход — по `operation_id`.
Для закрытия gap нужен controlled breaking change с миграцией generated layout и синхронизацией registry metadata/тестов/документации.

## Использованные источники (внутри репозитория)
- `src/apidev/application/services/diff_service.py`
- `src/apidev/core/rules/operation_id.py`
- `tests/unit/test_diff_service_transport_generation.py`
- `tests/integration/test_generate_roundtrip.py`
- `openspec/changes/001-contract-validation/artifacts/research/2026-02-27-external-api-codegen-baseline.md`
