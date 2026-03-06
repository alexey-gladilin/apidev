# Behavior Contract: Unified Diagnostics

## Командный контракт

### `apidev validate`
- machine-readable режим возвращает единый diagnostics envelope;
- в `summary` отражаются total/errors/warnings;
- при наличии ошибок exit code = `1`.

### `apidev diff`
- machine-readable режим возвращает diagnostics envelope + compatibility блок + `drift_status`;
- `drift_status=drift` не является ошибкой сам по себе (exit `0`), кроме strict policy gate;
- при policy-block (`strict` + breaking) exit code = `1`.

### `apidev gen --check`
- machine-readable режим возвращает diagnostics envelope + compatibility блок + `drift_status`;
- `drift_status=drift` приводит к exit `1`;
- `drift_status=no-drift` приводит к exit `0`.

### `apidev gen`
- machine-readable режим возвращает diagnostics envelope + compatibility блок + `drift_status` + `applied_changes`;
- `drift_status=error` приводит к exit `1`;
- успешный apply возвращает `drift_status=no-drift`, exit `0`.

## Нормализация diagnostics item
- Обязательные поля: `code`, `severity`, `location`, `message`.
- Опциональные поля: `category`, `detail`, `source`, `rule`, `hint`.
- Для типов diagnostics, где часть полей отсутствует в исходной модели, значения маппятся детерминированно через serializer policy.

## Детерминированность
- Diagnostics сортируются в стабильном порядке для одинакового входа.
- `summary` считается только из нормализованного массива diagnostics.
- Команда и режим должны влиять только на контекст envelope, а не на порядок item-ов.
