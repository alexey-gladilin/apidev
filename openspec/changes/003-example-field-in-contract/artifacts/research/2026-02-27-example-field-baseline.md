# Research Baseline: `example` field in contract schema (2026-02-27)

## Scope
- Проверить текущее поведение валидации контрактов относительно поля `example`.
- Проверить, попадает ли пример из contract schema в generation/OpenAPI pipeline.
- Зафиксировать минимальный список затронутых модулей и тестов.

## Evidence
1. `src/apidev/core/rules/contract_schema.py`
- `SCHEMA_ALLOWED_FIELDS = {"type", "properties", "items", "required", "description", "enum"}`.
- Поле `example` отсутствует в allowlist, поэтому будет классифицировано как unknown field через `_report_unknown_fields(...)`.

2. `docs/reference/contract-format.md`
- В разделе schema-фрагмента перечислены разрешенные поля без `example`.
- Документация согласована с текущей реализацией strict unknown-field policy.

3. `tests/unit/test_validate_service.py`
- Есть проверка на unknown fields (`contract.x_unknown`, `response.x_extra`, `errors[0].x_more`), но нет позитивных/негативных кейсов для `example`.

4. `src/apidev/application/services/diff_service.py`
- Fingerprint строится из `response.body` и `errors` целиком.
- При добавлении `example` в валидируемую модель fingerprint уже сможет учитывать это изменение, но только после разрешения поля в schema validation.

5. `src/apidev/templates/generated_openapi_docs.py.j2`
- Генерируется минимальный `paths` fragment (`operationId`, `summary`, `description`, `responses`), без включения schema examples.

6. `src/apidev/templates/generated_schema.py.j2`
- Генерируется `SCHEMA_FRAGMENT`, но нет отдельного контрактного поведения/гарантии по работе с examples.

## Baseline Conclusions
- На текущем baseline поле `example` фактически запрещено и блокируется на этапе validate.
- На текущем baseline отсутствует root-level endpoint блок примеров (например `examples.request/response/errors`), поэтому Swagger operation-level examples задавать декларативно нельзя.
- После расширения schema allowlist потребуется добавить explicit validation правилa для type/enum/container совместимости, чтобы сохранить strict contract quality.
- Generation/OpenAPI слой потребует явной фиксации поведения для deterministic exposure examples.

## Out of Scope for this research
- Поддержка `examples` (множественные примеры) и vendor extensions.
- Runtime-интерпретация examples вне generated metadata.

## Files likely impacted
- `src/apidev/core/rules/contract_schema.py`
- `src/apidev/core/models/contract.py`
- `src/apidev/application/services/diff_service.py`
- `src/apidev/templates/generated_openapi_docs.py.j2`
- `src/apidev/templates/generated_schema.py.j2`
- `tests/unit/test_validate_service.py`
- `tests/unit/test_diff_service_transport_generation.py`
- `tests/integration/test_generate_roundtrip.py`
- `docs/reference/contract-format.md`
