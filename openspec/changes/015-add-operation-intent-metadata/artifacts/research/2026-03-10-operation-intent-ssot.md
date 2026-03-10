# Research: operation intent and access pattern as APIDev SSOT

Дата: 2026-03-10

## Scope
- проверить, где `apidev` уже является SSOT для operation metadata;
- найти transport-related specs и tests, которые придется расширить;
- зафиксировать, почему method-only classification недостаточен для downstream-потребителей.

## Факты
- `apidev` уже хранит и публикует operation metadata через generated operation map и OpenAPI-related outputs.
- В проекте уже есть metadata поля уровня operation contract: `method`, `path`, `auth`, `summary`, `description`.
- Current specs `transport-generation` и tests around `operation_map`/OpenAPI явно закрепляют registry metadata как downstream-facing contract.
- В `apidev` testing policy есть отдельное обязательство покрывать generated/manual integration contract и metadata wiring.
- В существующих examples и default templates уже встречается `POST`-operation для `users/search`, то есть transport method сам по себе не кодирует business/consumer semantics достаточно точно.

## Проблема
Если downstream-классификация строится только по HTTP method, то:
- `POST`-search/read операции ошибочно выглядят как write/mutation;
- imperative read сценарии неотличимы от write-command сценариев;
- downstream-инструменты вынуждены вводить локальные эвристики, расходящиеся с SSOT.

## Вывод
Новый metadata contract должен жить в `apidev` operation contract и downstream-facing generated metadata.

Минимальный достаточный набор для первой версии:
- `intent`: `read | write`
- `access_pattern`: `cached | imperative | both | none`

Такой split решает обе задачи:
- семантика операции остается transport-independent;
- способ использования downstream-инструментом фиксируется явно и не выводится из метода или названия операции.

## Ограничения
- Первая версия вводит explicit metadata contract сразу и не сохраняет fallback для старых контрактов без нового metadata.
- В `apidev` нельзя hardcode runtime-specific terms вроде `useQuery` / `useMutation`; downstream mapping должен строиться поверх более нейтрального contract vocabulary.
