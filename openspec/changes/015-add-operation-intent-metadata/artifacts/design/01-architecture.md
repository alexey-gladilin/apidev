# Архитектура

## Level 1 — System Context
```mermaid
flowchart LR
  Analyst["Аналитик / Backend author"] --> Contract["APIDev YAML contract"]
  Contract --> APIDev["apidev validate / gen"]
  APIDev --> Metadata["Operation registry + OpenAPI metadata"]
  Metadata --> Downstream["uidev и другие downstream consumers"]
```

## Level 2 — Container
```mermaid
flowchart LR
  Contract["Operation contracts"] --> Loader["Contract loader / schema parse"]
  Loader --> Validator["Semantic validation"]
  Validator --> Registry["Generated operation registry"]
  Validator --> OpenAPI["Generated OpenAPI metadata"]
  Registry --> Consumers["Downstream consumers"]
  OpenAPI --> Consumers
```

## Level 3 — Component
```mermaid
flowchart LR
  Root["Contract root fields"] --> Intent["intent"]
  Root --> Access["access_pattern"]
  Intent --> Validator["Compatibility validator"]
  Access --> Validator
  Validator --> Required["Required metadata checks"]
  Required --> Registry["Operation map builder"]
  Validator --> Registry
  Validator --> OpenAPI["OpenAPI vendor extensions"]
```

## Notes
- `intent` и `access_pattern` остаются operation-level metadata.
- Metadata обязательна для каждого operation contract; implicit derivation по HTTP method не используется.
- Downstream читает итоговые значения из generated metadata, а не повторно решает их локально.
