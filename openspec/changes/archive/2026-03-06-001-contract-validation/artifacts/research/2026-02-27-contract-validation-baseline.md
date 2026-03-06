# Research: Contract Validation Baseline (Fact-Only)

Дата: 2026-02-27  
Scope: текущее состояние validate-пайплайна в `apidev` без рекомендаций.

## Подтвержденные факты
- `YamlContractLoader.load` проходит по `*.yaml` внутри contracts root, читает `yaml.safe_load` и формирует `EndpointContract` c default-значениями (`method`, `path`, `auth`, `response`, `errors`) без отдельного strict schema-контракта на обязательные поля.  
  Source: `src/apidev/infrastructure/contracts/yaml_loader.py`
- `build_operation_id` вычисляет ID из относительного пути файла; `ensure_unique_operation_ids` добавляет только строковую ошибку вида `Duplicate operation_id: ...` при коллизии.  
  Source: `src/apidev/core/rules/operation_id.py`
- `ValidateService.run` загружает конфиг, резолвит пути, загружает операции и наполняет `ValidationResult.errors` только результатом `ensure_unique_operation_ids`; дополнительных semantic/schema checks в сервисе сейчас нет.  
  Source: `src/apidev/application/services/validate_service.py`
- `ValidationResult` представлен как dataclass с `operations: list[Operation]` и `errors: list[str]`; diagnostics codes и структурированная модель отсутствуют.  
  Source: `src/apidev/application/dto/diagnostics.py`
- CLI команда `validate` печатает ошибки как human-readable текст (`[red]ERROR[/red] ...`) и завершает процесс с `typer.Exit(1)` при наличии ошибок; `--json` режим отсутствует.  
  Source: `src/apidev/commands/validate_cmd.py`
- Конфиг дефолтно использует `.apidev/contracts` и резолвит относительные пути от корня проекта до абсолютных перед загрузкой контрактов.  
  Source: `src/apidev/core/models/config.py`, `src/apidev/application/dto/resolved_paths.py`, `src/apidev/infrastructure/config/toml_loader.py`
- Unit-покрытие validate в текущем виде проверяет позитивный сценарий загрузки одного валидного контракта; отдельные негативные кейсы schema/semantic пока не зафиксированы.  
  Source: `tests/unit/test_validate_service.py`
