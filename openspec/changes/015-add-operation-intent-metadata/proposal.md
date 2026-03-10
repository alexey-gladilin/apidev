# Change: SSOT metadata для семантики и client-access паттерна операции

## Почему
`apidev` уже является source of truth для transport metadata операции: `method`, `path`, `auth`, request/response shape, OpenAPI hints и generated operation map. Но для downstream-инструментов этого недостаточно, когда transport-метод не совпадает с семантикой использования.

Главный проблемный сценарий: `POST` может использоваться не для модификации, а для чтения данных с тяжелым фильтром в `body` (`search`, `report`, `preview`, `calculate`). В таком случае downstream вроде `uidev` не может надежно вывести из `method`:
- операция семантически читает или пишет данные;
- downstream должен генерировать cache-oriented wrapper или imperative wrapper;
- нужно ли генерировать оба варианта или вообще не генерировать hook layer.

Если этот смысл не хранится в `apidev`, каждый downstream начинает додумывать intent локально и расходится с SSOT.

## Что меняется
- В operation contract `apidev` вводятся два новых top-level metadata поля:
  - `intent`: `read | write`
  - `access_pattern`: `cached | imperative | both | none`
- `intent` фиксирует семантику операции как SSOT для downstream-потребителей.
- `access_pattern` фиксирует рекомендуемый consumer-facing режим использования операции без привязки к конкретному runtime-фреймворку.
- `intent` и `access_pattern` становятся обязательной частью operation contract; legacy authoring без этих полей больше не поддерживается.
- `apidev validate` получает обязанность валидировать наличие новых полей, допустимые значения и их совместимость.
- Generated operation metadata и OpenAPI vendor extensions начинают детерминированно публиковать `intent` и `access_pattern`.
- Документация contract format и examples получает явные примеры:
  - `POST`-read operation с `intent=read`
  - imperative read без auto-cache semantics
  - invalid combinations, которые отклоняются validate-пайплайном

## Влияние
- Affected specs:
  - `transport-generation`
  - `contract-validation-hardening`
  - `contract-examples`
  - `diff-gen-safety`
- Affected docs:
  - `docs/reference/contract-format.md`
  - `docs/reference/cli-contract.md`
  - authoring examples for operation contracts
- Affected code (planned):
  - contract models / YAML loader / validation
  - generated operation map / OpenAPI metadata
  - integration and contract test matrix
  - `.apidev/contracts/*` и связанные repo-local fixtures/examples

## Ожидаемый результат
Автор контракта сможет явно описать:
- что операция семантически делает: читает или пишет;
- как downstream должен использовать ее по умолчанию: cache-oriented, imperative, оба режима или без generated consumer wrapper.

Для downstream-инструментов это означает:
- `POST`-search больше не обязан автоматически трактоваться как mutation;
- `GET`-read может оставаться cached default;
- imperative read сценарии становятся first-class metadata, а не ad-hoc эвристикой.
- in-repo contract inventory должен быть мигрирован на explicit metadata до прохождения validate/generate pipeline.
  Минимальный scope для этого change: `.apidev/contracts/system/health.yaml` и `.apidev/contracts/users/search.yaml`.

## Связанные артефакты
- Research: [operation-intent-ssot](./artifacts/research/2026-03-10-operation-intent-ssot.md)
- Design: [design.md](./design.md)
- Design artifacts:
  - [01-architecture](./artifacts/design/01-architecture.md)
  - [02-behavior](./artifacts/design/02-behavior.md)
  - [03-decisions](./artifacts/design/03-decisions.md)
  - [04-testing](./artifacts/design/04-testing.md)
- Plan:
  - [README](./artifacts/plan/README.md)
  - [phase-01](./artifacts/plan/phase-01.md)
  - [phase-02](./artifacts/plan/phase-02.md)
  - [phase-03](./artifacts/plan/phase-03.md)
  - [implementation-handoff](./artifacts/plan/implementation-handoff.md)

## Границы и non-goals
- Change не вводит transport behavior вне уже существующего contract format.
- Change не делает `apidev` владельцем React Query/Vue Query API; downstream mapping остается обязанностью downstream-инструмента.
- Change не сохраняет compatibility fallback по HTTP method; целевой explicit metadata contract вводится сразу.
- Change не выполняет implementation; это отдельная implement phase после review/approval.
