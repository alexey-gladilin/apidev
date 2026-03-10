# Implementation Handoff

## Статус
Implementation phase доведена до финального verification/handoff этапа. Core code, generated metadata contract, migration of repo-local fixtures/templates и verification block уже реализованы в этом change set.

## Что реализовано
- root-level operation metadata `intent` и `access_pattern` обязательны для каждого operation contract;
- `validate`, loader и graph path используют explicit metadata contract без fallback по HTTP method;
- semantic validation фиксирует allowed values и compatibility matrix;
- generated `operation_map` публикует `intent` и `access_pattern` как SSOT metadata;
- generated OpenAPI публикует `x-apidev-intent` и `x-apidev-access-pattern`;
- repo-local contracts, fixtures, examples и templates мигрированы на explicit-only shape;
- downstream integration tests подтверждают, что consumer paths читают metadata из generated artifacts без reparsing YAML.

## Downstream contract
- `OPERATION_MAP[operation_id]["intent"]` -> `read | write`
- `OPERATION_MAP[operation_id]["access_pattern"]` -> `cached | imperative | both | none`
- OpenAPI vendor extensions:
  - `x-apidev-intent`
  - `x-apidev-access-pattern`
- Downstream consumers вроде `uidev` могут делать mapping напрямую по этим полям без эвристики по `method`.

## Migration impact
- Старые контракты без `intent`/`access_pattern` детерминированно отклоняются в `validate`, `diff`, `gen`, `gen --check`, loader и graph path.
- Новые и изменяемые контракты authoring-ятся только с explicit metadata.
- Repo-local templates и starter contracts уже публикуют explicit metadata.
- External consumers вне репозитория в scope migration не входили; им нужен переход на новый field contract при обновлении на этот change.

## Verification status
- Focused verification для schema/semantic/generation/runtime paths пройдена.
- `openspec validate 015-add-operation-intent-metadata --strict --no-interactive` проходит.
- Full `uv run pytest` находится в финальном gate этой волны и должен быть зелёным перед окончательным closeout.

## Residual risks
- external downstream consumers могут по-разному интерпретировать `access_pattern`, если не закрепят свой mapping в своей документации;
- при появлении новых repo-local examples/tests нужно продолжать explicit-only discipline, иначе full suite снова будет ловить legacy fixtures;
- если появятся дополнительные consumer tools поверх OpenAPI, им нужно использовать vendor extensions как SSOT, а не эвристики по transport method.
