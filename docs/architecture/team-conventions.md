# Командные Соглашения

Статус: `Guide`

Это краткий operational cheat sheet для ежедневной разработки. Полные нормы находятся в `architecture-rules.md`, а подробные rationale и примеры — в `patterns-and-naming.md`.

## Язык

- Документация и process-docs пишутся на русском языке.
- Комментарии, docstrings, identifiers, test names, CLI flags и diagnostic codes пишутся на английском языке.

## Quick rules по ответственности

- `commands/*` — CLI вход, UX и composition root.
- `application/*` — orchestration без concrete I/O.
- `core/*` — доменные понятия, правила, порты, инварианты.
- `infrastructure/*` — форматы, filesystem, шаблоны и внешние зависимости.

## Quick rules по неймингу

- `*Service` — orchestration/use-case.
- `*Port` — абстракция.
- `*Loader`, `*Renderer`, `*Writer`, `*FileSystem` — concrete adapters.
- `*Result`, `*Plan`, `*Config`, `*Paths`, `*Issue`, `*Error` — DTO и state types.
- Модули — `snake_case`.
- Entry-point модули CLI следуют шаблону `<verb>_cmd.py`.
- В документации используем `generated_dir`; legacy identifier `generated_root` допустим во внутреннем коде/тестах как техническое имя того же пути.

## Что проверять в review

- Не утекает ли business logic в `commands/*`.
- Не тянет ли `core/*` raw parsing или direct I/O.
- Соответствует ли имя модуля и типа фактической ответственности.
- Не появился ли `helpers` или `misc` вместо предметного имени.
- Соблюдается ли языковая политика.

## Связанные документы

- `docs/architecture/architecture-rules.md`
- `docs/architecture/patterns-and-naming.md`
- `docs/reference/glossary.md`
