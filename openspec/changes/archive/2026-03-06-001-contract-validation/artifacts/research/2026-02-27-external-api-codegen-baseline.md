# Исследование: baseline для шаблонов кодогенерации на основе `external_assortment_api/api`

Статус: `Research Artifact`
Дата: 27 февраля 2026
Источник анализа: `<external-repository>/src/external_assortment_api/api`

## Цель

Зафиксировать практики структуры и стиля в существующем FastAPI-проекте, сопоставить их с целями APIDev и определить, какие элементы должны попасть в шаблоны кодогенерации, а какие должны быть ограничены через guardrails.

## 1. Наблюдения по структуре

### 1.1 Модульная организация

В каталоге `api/` наблюдается устойчивый feature-first паттерн: один доменный модуль на бизнес-область.

Типичный состав модуля:

- `routes.py`
- `schemas.py`
- `services.py`
- `repositories.py`
- `response_config.py` (опционально)
- `config.py` и `openapi_docs.py` для более сложных endpoint-ов (`search`, `assortment_matrices`)

Покрытие этим паттерном высокое (например: `assortment`, `availability`, `clustering`, `geography`, `quotas`, `rebalancing`, `scenario`, `search`, `user`).

### 1.2 Composition root и сборка API

`main.py` выполняет роль composition root:

- подключение всех feature routers;
- кастомные exception handlers;
- post-processing OpenAPI (добавление response metadata и query parameters для динамических endpoint-ов).

Вывод для APIDev: генератор должен поддерживать как минимум два артефакта уровня приложения:

- реестр/подключение роутеров;
- централизованный слой ошибок/ответов.

### 1.3 DI и зависимости

Используется FastAPI DI через `Depends` + type alias (`SessionDep`, `UserRkDep`).

Вывод для APIDev:

- шаблоны должны генерировать типизированные dependency aliases;
- маршруты должны получать зависимости через DI, а не через глобальные singletons.

## 2. Наблюдения по стилю и кодовым практикам

## 2.1 Сильные стороны (тиражируемые)

- Четкое разделение ролей: transport (`routes`) vs orchestration (`services`) vs data access (`repositories`).
- Активное использование Pydantic-схем для request/response.
- Централизация формата ошибок через `ErrorHandler`.
- Явная настройка OpenAPI и response templates.
- SQL с параметризацией (`text(...)` + bind params), без строковой подстановки значений.

## 2.2 Вариативность и неоднородность (что нужно нормализовать в генераторе)

- Смешение `Depends(ServiceClass)` и ручного создания `Service(session)` в route handlers.
- Непоследовательный naming параметров: одновременно `matrix_rk` и `matrixRk`, `scenarioRk`, `parentRk`.
- Смешение стилей Pydantic (`Config` и `ConfigDict`), неединообразные `schema_extra/json_schema_extra`.
- Локальные орфографические и нейминговые дефекты (`GetSubmatrixResponce`, `marices_reset`, `manal`, `transer`, и т.д.).
- Встречаются русские комментарии внутри code artifacts, что нарушает англоязычность кода.
- Есть импорты через `src.external_assortment_api...` рядом с обычными абсолютными импортами пакета.

Вывод для APIDev: генерация должна быть opinionated и формировать единый стиль, даже если исходный проект исторически неоднороден.

## 2.3 Граница generated/manual

Из observed практик:

- сервисы и репозитории содержат изменчивую бизнес-логику и SQL, то есть должны оставаться manual-owned;
- transport слой во многом шаблонный и повторяемый.

Это напрямую совпадает с vision APIDev: генерировать стабильные transport/contract слои, но не бизнес-правила.

## 3. Сопоставление с целями APIDev

Сверка выполнена против:

- `docs/product/vision.md`
- `docs/roadmap.md` (Этап B — Transport Generation MVP+)

### 3.1 Что хорошо ложится в зону кодогенерации

- Каркас feature-модуля API (`routes + schemas + wiring`),
- operation map / router registry,
- базовые error response contracts и OpenAPI metadata hooks,
- единый dependency wiring шаблон,
- скелеты request/response моделей.

### 3.2 Что НЕ должно генерироваться

- SQL запросы и repository internals,
- бизнес-валидации в service-логике,
- доменные side effects,
- проектно-специфичные security/policy детали.

Это согласуется с разделом "Что APIDev не генерирует" из `docs/product/vision.md`.

## 4. Требования к шаблонам кодогенерации (derive из анализа)

## 4.1 Обязательный baseline шаблона feature API

Каждый generated feature-модуль должен поддерживать:

- `routes.py` с router prefix/tags и декларативными endpoint signatures;
- `schemas.py` с request/response моделями и единым стилем Pydantic;
- `errors.py` или подключение к централизованным response templates;
- `wiring` для подключения в общий API registry.

## 4.2 Code-style guardrails для генератора

Генератор должен принудительно обеспечивать:

- `snake_case` для параметров Python-кода;
- единый стиль Pydantic (рекомендуется Pydantic v2 `ConfigDict`);
- единый стиль импортов (без `src.`-префикса в runtime imports);
- шаблон англоязычных docstrings/comments в code artifacts;
- единообразный паттерн DI (предпочтительно через aliases + `Depends`).

## 4.3 OpenAPI/Errors baseline

Генерация должна включать:

- структурированные error responses через единый контракт;
- возможность подключать endpoint-level custom responses;
- предсказуемую точку расширения OpenAPI для сложных endpoint-ов.

## 5. Риски для этапа кодогенерации

- Риск переноса исторической неоднородности проекта в generated code.
- Риск смешения ownership между generated и manual слоями.
- Риск дрейфа именований и несовместимых style-конвенций между модулями.

Снижение рисков:

- фиксированный набор шаблонных артефактов + style guardrails;
- явный generated/manual boundary в структуре целевого проекта;
- contract tests на шаблоны и snapshot-проверки generated output.

## 6. Артефакты-выходы для дальнейших фаз

Этот документ используется как вход для:

- проектирования шаблонов transport generation в Этапе B;
- декомпозиции задач implementation-фазы кодогенерации;
- формирования acceptance criteria на консистентность generated output.

Связанный roadmap reference:

- `docs/roadmap.md`, раздел "Этап B — Transport Generation MVP+".

