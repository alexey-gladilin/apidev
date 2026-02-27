# Поведение: Transport Generation MVP+

## 1. Внешнее поведение `apidev gen`
- При валидном наборе контрактов generation формирует deterministic transport output для registry/router/models/errors.
- При повторном запуске без изменений контрактов артефакты остаются byte-stable.
- В check-режиме `apidev gen --check` фиксируется drift без записи файлов.

## 2. Контракт operation registry
- Registry является generated-артефактом с устойчивой структурой и порядком записей.
- Запись registry связывает `operation_id` с HTTP metadata и ссылками на transport artifacts.
- Registry достаточен для runtime wiring и тестовых проверок без runtime-парсинга YAML-контрактов.

## 3. Контракт handler bridge
- Generated transport определяет стабильные точки вызова manual handlers.
- Bridge-сигнатуры являются deterministic output и не зависят от ручного форматирования.
- Отсутствующие bridge-реализации проявляются детерминированно в интеграционном контуре, а не через silent fallback.

## 4. Граница ownership
- Generated-файлы ограничены transport-контрактами, routing-описанием и schema metadata.
- Business logic, policy и data access остаются в manual-owned слоях.
- Генерация не изменяет файлы вне configured generated root.
