# Поведение: Domain-first Layout

## 1. `apidev diff`
- Показывает изменения относительно domain-first canonical output.

## 2. `apidev gen --check`
- Возвращает `drift`, если generated output не соответствует domain-first layout.
- Возвращает `no-drift` при неизменных контрактах и корректном domain-first output.

## 3. `apidev gen`
- Записывает generated артефакты только в domain-first структуре путей.

## 4. Registry/Bridge metadata
- Содержит domain-qualified module references, пригодные для runtime wiring.

## 5. Target app integration
- Endpoint registration выполняется в manual composition root через generated registry metadata.
- Auth wiring выполняется manual зависимостями на основе contract metadata (`public`/`bearer`).
- Error mapping выполняется manual policy-слоем, generated слой не содержит domain semantics.
- OpenAPI wiring использует generated builder (`build_openapi_paths`) и manual openapi composition hook.
