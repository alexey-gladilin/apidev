# Тестирование

## Обязательный минимум
1. Unit: path planning для routers/models в domain-first layout.
2. Unit: deterministic ordering generation plan на неизменных контрактах.
3. Contract: operation map/bridge metadata содержит domain-qualified module paths.
4. Integration: generated artifacts компилируются в новом layout.
5. Integration: повторный `gen --check` после `gen` на неизменных контрактах возвращает `no-drift`.

## Regression focus
- unchanged contracts должны давать byte-stable output;
- registry/module references должны быть согласованы между diff/gen и шаблонами.
