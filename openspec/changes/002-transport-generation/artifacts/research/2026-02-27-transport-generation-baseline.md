# Исследование: baseline текущего transport generation в `apidev`

Статус: `Research Artifact`
Дата: 27 февраля 2026
Источник анализа: репозиторий `apidev` (ветка workspace на дату исследования)

## Область и метод

Исследование фиксирует фактическое состояние generation-пайплайна и шаблонов transport-артефактов для подготовки этапа B (`Transport Generation MVP+`).
Документ содержит только наблюдения по коду и документации без проектных решений implement-фазы.

## 1. Факты по текущему generation pipeline

### 1.1 DiffService формирует ограниченный набор артефактов

В `src/apidev/application/services/diff_service.py` зафиксированы два типа generated output:
- `operation_map.py` через шаблон `generated_operation_map.py.j2`;
- один router-файл на `operation_id` через `generated_router.py.j2`.

В текущей реализации нет формирования request/response/error model-файлов в generation plan.

### 1.2 GenerateService применяет только `ADD`/`UPDATE`

`src/apidev/application/services/generate_service.py` применяет изменения только типов `ADD` и `UPDATE`, режим `--check` возвращает drift-флаг без записи.

### 1.3 CLI generation surface стабилен

`src/apidev/commands/generate_cmd.py` использует существующую командную поверхность `apidev gen` (и alias `generate` по CLI-контракту), вызывает `GenerateService.run(...)`, печатает `Applied changes: N`, при drift в check-режиме завершает работу с exit code `1`.

## 2. Факты по шаблонам transport-артефактов

### 2.1 Router template является skeleton-уровнем

`src/apidev/templates/generated_router.py.j2` содержит только заголовок generated-файла и metadata-комментарии (`operation_id`, source contract, method/path).

### 2.2 Schema template минимальный

`src/apidev/templates/generated_schema.py.j2` содержит только заголовок generated-файла без model-контента.

### 2.3 Operation map template содержит mapping operation_id -> METHOD PATH

`src/apidev/templates/generated_operation_map.py.j2` формирует словарь `OPERATION_MAP` со строковым значением метода и пути.

## 3. Сопоставление с roadmap snapshot

В `docs/roadmap.md` (снимок состояния от 26 февраля 2026) этап B требует:
- request/response/error model generation;
- минимально runnable transport layer;
- стабильный operation registry и handler bridge contract.

Зафиксированное в коде состояние соответствует отмеченному gap в roadmap: transport generation находится на skeleton-уровне.

## 4. Связанные baseline-артефакты

Для style/structure ориентиров перед implement-фазой roadmap ссылается на внешний артефакт:
`openspec/changes/001-contract-validation/artifacts/research/2026-02-27-external-api-codegen-baseline.md`.

Этот baseline существует в репозитории и может быть использован как reference при проектировании template guardrails, не изменяя фактические наблюдения текущего pipeline.
