# Поведение: REMOVE в drift governance

## 1. Планирование изменений
- `DiffService` формирует expected artifact set из текущих контрактов.
- Для файлов внутри generated root, отсутствующих в expected set, формируется `REMOVE`.
- Состав плана нормализуется в стабильном порядке: `ADD`, `UPDATE`, `REMOVE`, `SAME` (детерминированный sort по path внутри типа).

## 2. Поведение `apidev diff`
- Режим read-only.
- Drift считается обнаруженным, если есть хотя бы один `ADD`, `UPDATE` или `REMOVE`.
- Exit semantics сохраняются: при drift -> `0`, при no-drift -> `0`, при pipeline error -> `1`.
- Для `REMOVE` в выводе печатается строка операции и путь stale файла.

## 3. Поведение `apidev gen --check`
- Режим read-only.
- Drift считается обнаруженным, если есть хотя бы один `ADD`, `UPDATE` или `REMOVE`.
- При drift команда возвращает `exit 1`.
- При отсутствии drift команда возвращает `exit 0`.

## 4. Поведение `apidev gen` (apply)
- Применяются `ADD`, `UPDATE`, `REMOVE`.
- Любая операция за пределами generated root блокируется safety-ошибкой.
- Успешный apply возвращает `drift-status: no-drift`.
- Ошибка apply возвращает `drift-status: error`.

## 5. Conflict и diagnostic сценарии
- stale artifact отсутствует к моменту apply: диагностируется как remove-conflict, classified как `error`.
- попытка remove вне generated root: диагностируется как boundary-violation, classified как `error`.
- diagnostics содержат stable code, location (path), detail (причина/контекст).

## 6. Трассировка на requirements
- `REQ-1`: секции 1, 6
- `REQ-2`: секции 2, 3
- `REQ-3`: секция 4
- `REQ-4`: секции 1, 5
