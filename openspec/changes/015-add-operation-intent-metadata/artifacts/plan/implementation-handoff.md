# Implementation Handoff

## Статус
Proposal package готовит change к отдельной implement phase. Production code в этот пакет не входит.

## Что должен дать implement phase
- новые root-level operation metadata поля `intent` и `access_pattern`;
- validate support для allowed values и compatibility matrix;
- generated metadata contract в operation map и OpenAPI vendor extensions;
- tests для explicit metadata и deterministic migration failures.

## Migration impact
- Старые контракты без `intent`/`access_pattern` должны быть мигрированы; без этого validate/generate больше не проходят.
- Новые и изменяемые контракты authoring-ятся только с explicit metadata.
- Downstream consumers могут начать читать новые SSOT поля без локальной эвристики по HTTP method.

## Residual risks
- breaking migration может затронуть существующий contract inventory и templates;
- downstream consumers могут по-разному интерпретировать `access_pattern`, если не зафиксировать mapping в своей документации;
- migration effort может потребовать синхронного обновления примеров, fixture-файлов и generated snapshots.
