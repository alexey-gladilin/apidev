# Соглашение по именованию команд

Чтобы избежать разнобоя, для всех новых команд используется единый шаблон:

- `/<domain>-<action>`
- при необходимости: `/<domain>-<action>-<mode>`

## Домены

- `openspec-*` — команды OpenSpec-потока.
- `bugfix-*` — оперативные исправления без OpenSpec change-id.
- `prompt-*` — утилиты по работе с промптами.

## Правила

1. `name` и `id` в frontmatter должны совпадать по смыслу и отличаться только `/` в `name`.
2. Имя файла должно совпадать с `id`: `<id>.md`.
3. Не использовать смешанные схемы вроде `verb-noun` и `noun-verb` в одном домене.
4. Для режимов использовать суффикс: `-single`, `-batch`, `-strict` и т.д.
5. Legacy-команды допускаются только с явной пометкой `Legacy` в описании.

## Текущие канонические команды

- `/openspec-proposal`
- `/openspec-implement`
- `/openspec-implement-single`
- `/openspec-archive`
- `/bugfix-implement`
- `/prompt-improve`
- `/prompt-baseline-refresh`
