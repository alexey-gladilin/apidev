# Change: Optional `example` field in API contract schema

## Почему
Сейчас контрактный формат запрещает любые неизвестные поля в schema-фрагментах, поэтому попытка добавить `example` приводит к `SCHEMA_UNKNOWN_FIELD` и блокирует `apidev validate`.
Это затрудняет поддержку понятной API-документации и не позволяет декларативно задавать примеры payload на уровне контракта.

## Что изменится
- Добавляется поддержка опционального поля `example` в schema-фрагментах (`response.body`, `errors[*].body`, вложенные `properties`, `items`).
- Добавляется endpoint-level блок `examples` в root контракта для полноценных operation payload examples в Swagger/OpenAPI.
- Формализуются правила валидации `example` (типовая совместимость с `type`, `enum`, контейнерными структурами).
- Генерация transport/OpenAPI metadata расширяется так, чтобы `example` из контракта попадал в generated артефакты детерминированно.
- Обновляются reference docs и тестовая матрица на positive/negative/regression сценарии для `example`.

## Влияние
- Затронутые спеки: `contract-examples` (новая capability в рамках change delta).
- Затронутый код:
  - `src/apidev/core/rules/contract_schema.py`
  - `src/apidev/core/models/contract.py`
  - `src/apidev/application/services/diff_service.py`
  - `src/apidev/templates/generated_openapi_docs.py.j2`
  - `src/apidev/templates/generated_schema.py.j2`
  - `tests/unit/test_validate_service.py`
  - `tests/unit/test_diff_service_transport_generation.py`
  - `tests/integration/test_generate_roundtrip.py`
  - `docs/reference/contract-format.md`

## Linked Artifacts
- Research: [artifacts/research/2026-02-27-example-field-baseline.md](./artifacts/research/2026-02-27-example-field-baseline.md)
- Design package: [artifacts/design/README.md](./artifacts/design/README.md)
- Plan package: [artifacts/plan/README.md](./artifacts/plan/README.md)
- Spec delta: [specs/contract-examples/spec.md](./specs/contract-examples/spec.md)

## Границы этапа
Эта change-заявка описывает только Proposal/Design/Plan этапы.
Implementation выполняется отдельной командой (`/openspec-implement` или `/openspec-implement-single`) после review/approval.
