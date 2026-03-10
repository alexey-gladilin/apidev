# Поведение

## Canonical examples

### Read + cached
```yaml
method: GET
path: /v1/users/{user_id}
intent: read
access_pattern: cached
```

### Read + imperative
```yaml
method: POST
path: /v1/users/search
intent: read
access_pattern: imperative
```

### Read + both
```yaml
method: POST
path: /v1/reports/preview
intent: read
access_pattern: both
```

### Write + imperative
```yaml
method: POST
path: /v1/users
intent: write
access_pattern: imperative
```

### Write + none
```yaml
method: DELETE
path: /v1/users/{user_id}
intent: write
access_pattern: none
```

## Invalid examples

### Write + cached
```yaml
intent: write
access_pattern: cached
```

### Write + both
```yaml
intent: write
access_pattern: both
```

## Missing metadata behavior
- if explicit metadata is absent:
  - validation fails with required-field diagnostics
  - generated metadata is not emitted for invalid operation contracts

## Generated metadata expectations
- operation registry contains explicit `intent`
- operation registry contains explicit `access_pattern`
- OpenAPI contains `x-apidev-intent`
- OpenAPI contains `x-apidev-access-pattern`
