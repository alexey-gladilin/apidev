# Implementation Handoff

## Цель
Перевести `apidev` на канонический конфигурационный контракт с секциями `paths/inputs/generator/evolution/openapi`, без `version` и без backward compatibility.

## Что должен сделать implement-этап
1. Обновить модель и загрузчик конфигурации.
2. Обновить `init` для materialization нового формата.
3. Обновить тесты и документацию.
4. Прогнать quality gates и strict OpenSpec validate.

## Критерии готовности
- Loader принимает только новый формат.
- Ошибки по legacy-ключам детерминированы.
- Все команды используют единый resolved config.
- Тесты и линтеры проходят.
