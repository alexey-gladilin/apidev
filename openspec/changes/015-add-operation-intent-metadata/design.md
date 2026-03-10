## Контекст
`apidev` уже экспортирует operation metadata в generated registry и OpenAPI fragments, а downstream-инструменты семейства dev-tools читают эти данные как SSOT. Сейчас в contract format есть `method`, `path`, `auth`, request/response shape, но нет явного признака:
- семантически читает операция данные или модифицирует;
- downstream должен использовать ее как cache-oriented operation или imperative operation.

Из-за этого downstream вроде `uidev` вынужден классифицировать операции по HTTP method, что дает ложные срабатывания для `POST`-read сценариев (`search`, `lookup`, `preview`, `report`).

Research artifact: [operation-intent-ssot](./artifacts/research/2026-03-10-operation-intent-ssot.md)

## Цели / Не цели
- Цели:
  - сделать `apidev` SSOT для operation intent и default access pattern;
  - публиковать новые metadata в validate/generate/OpenAPI outputs;
  - дать downstream-потребителям deterministic contract без локальных эвристик.
  - ввести explicit metadata contract сразу как обязательный baseline для всех operation contracts.
- Не цели:
  - встраивать в `apidev` runtime-специфичные генераторы client hooks;
  - автоматически угадывать intent по `summary` / `operation_id` / path tokens.

## Ключевые решения
- Решение: новые поля добавляются как top-level metadata operation contract: `intent` и `access_pattern`.
  - Почему: это сохраняет читаемость YAML и соответствует уже существующему flat metadata shape (`method`, `path`, `auth`, `summary`, `description`).

- Решение: `intent` и `access_pattern` разделяются.
  - Почему: семантика операции и способ downstream-использования не одно и то же. `POST`-read должен быть возможен без подмены transport semantics.

- Решение: `intent` ограничивается значениями `read | write`.
  - Почему: первая версия должна быть минимальной и достаточно широкой для downstream-классификации без лишней таксономии.

- Решение: `access_pattern` ограничивается значениями `cached | imperative | both | none`.
  - Почему: это нейтральнее, чем hardcode `query | mutation`, и достаточно выразительно для downstream mapping.

- Решение: `intent` и `access_pattern` обязательны для каждого operation contract.
  - Почему: команда не поддерживает backward compatibility для legacy authoring и хочет сразу зафиксировать целевой contract без mixed mode.

## Нормативный contract shape
Новые поля находятся на root-level operation contract:

```yaml
method: POST
path: /v1/users/search
auth: bearer
summary: Search users
description: Returns users by complex filter
intent: read
access_pattern: imperative
request:
  body:
    type: object
    properties:
      query:
        type: string
response:
  status: 200
  body:
    type: object
```

Допустимые значения:
- `intent`:
  - `read`
  - `write`
- `access_pattern`:
  - `cached`
  - `imperative`
  - `both`
  - `none`

## Совместимость intent и access_pattern
Первая версия фиксирует такие правила:
- `intent=read`:
  - допускает `cached`, `imperative`, `both`, `none`
- `intent=write`:
  - допускает `imperative`, `none`
  - не допускает `cached`
  - не допускает `both`

## Обязательность metadata
Если хотя бы одно из полей `intent` или `access_pattern` отсутствует, contract считается невалидным.
`apidev validate` обязан выдавать явную structured diagnostic, требующую миграции operation contract на explicit metadata.

## Generated metadata contract
`apidev gen` должен детерминированно публиковать эти поля:
- в generated operation map;
- в generated OpenAPI vendor extensions;
- в любых downstream-facing metadata structures, которые уже строятся из operation registry.

Предлагаемый vendor extension contract:
- `x-apidev-intent`
- `x-apidev-access-pattern`

## Validation contract
`apidev validate` обязан:
- принимать новые поля без unknown-field diagnostics;
- требовать явного присутствия `intent` и `access_pattern` в каждом operation contract;
- отклонять значения вне allowed set;
- отклонять несовместимые комбинации `intent/access_pattern`;
- сохранять machine-readable diagnostics contract.

## Влияние на downstream
Downstream-инструмент может теперь делать mapping так:
- `intent=read`, `access_pattern=cached` -> cache-oriented wrapper
- `intent=read`, `access_pattern=imperative` -> imperative read wrapper
- `intent=read`, `access_pattern=both` -> оба варианта
- `intent=write`, `access_pattern=imperative` -> write command wrapper
- `intent=write`, `access_pattern=none` -> no generated wrapper

## Риски / Trade-offs
- Риск: авторы контрактов начнут путать intent и transport method.
  - Смягчение: examples и validation rules должны явно показывать `POST`-read сценарий как валидный, но осознанный.

- Риск: downstream начнут интерпретировать `access_pattern` слишком runtime-specific способом.
  - Смягчение: в `apidev` термин остается нейтральным (`cached` / `imperative`), без упоминания конкретной client library.

- Риск: внедрение станет breaking change для текущего contract inventory.
  - Смягчение: implement phase должна включать явную миграцию `.apidev/contracts/system/health.yaml`, `.apidev/contracts/users/search.yaml`, repo-local fixtures/examples и templates в том же change set. External consumers вне репозитория не входят в scope migration.

## Migration Plan
1. Добавить root-level metadata поля в contract schema и docs.
2. Сделать validation strict по наличию и совместимости новых полей.
3. Обновить generated metadata contract и OpenAPI vendor extensions.
4. Мигрировать `.apidev/contracts/system/health.yaml`, `.apidev/contracts/users/search.yaml`, repo-local fixtures/examples и templates на explicit metadata.
5. Добавить examples для `GET`-read, `POST`-read, `POST`-write.
6. Добавить contract/integration tests для explicit metadata, JSON diagnostics contract и migration failures.
