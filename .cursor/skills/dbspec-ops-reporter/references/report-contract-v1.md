# DBSpec Report Contract v1

Use this contract for every DBSpec operational report.

## Language Rules

- Human-facing Markdown report (`*.md`) must be written in Russian.
- English is allowed in Markdown only for technical literals: command names, paths, codes, schema keys.
- JSON is schema-first; text values may be Russian.

## Determinism Rules

1. Prohibit ad-hoc temporary scripts for report logic.
2. Use fixed command sequences from `.cursor/commands/dbspec-*.md`.
3. Normalize infra/runtime failures into `DBS-ENV-*` findings.
4. Do not set `status=ok` if any required command has non-zero `exit_code`.

## Header Fields

- `report_version`: must be `dbspec-report/v1`
- `report_type`: `env_readiness|naming_consistency|migration_health|ssot_db_consistency|combined_health|delta_health`
- `generated_at`: ISO-8601 UTC timestamp
- `project_root`: absolute or workspace-relative path
- `tooling`: `dbspec` command mode used (`binary` or `uv-run-module`)
- `status`: `ok|warning|error`
- `score`: integer 0..100

## Scope And Criteria (Required)

Every report must include:

- `what_was_checked`: explicit checks performed in this run
- `criteria_used`: explicit criteria/rules used
- `execution_context`: execution constraints and environment notes

Avoid vague entries like "standard checks".

## Findings Schema

Each finding must include:

- `code`
- `severity` (`error|warning|info`)
- `object_type`
- `object_ref`
- `rule`
- `evidence`
- `recommended_action`

## Command Evidence Schema

Each row must include:

- `command`
- `exit_code`
- `summary`

## Prioritization And Structure

Required blocks for Markdown reports:

1. `Что проверялось`
2. `Критерии проверки`
3. `Ограничения и контекст выполнения`
4. `Краткое резюме`
5. `Группы проблем`
6. `Замечания`
7. `Подтверждение команд`
8. `Топ-5 действий`
9. `Следующие действия`

`Группы проблем` must aggregate findings by rule group with counts.
`Топ-5 действий` must be prioritized by impact and effort.

## Markdown Template (Required)

```markdown
# Операционный отчет DBSpec

- report_version: dbspec-report/v1
- report_type: <type>
- generated_at: <ISO-8601>
- project_root: <path>
- tooling: <binary|uv-run-module>
- status: <ok|warning|error>
- score: <0-100>

## Что проверялось

1. ...

## Критерии проверки

1. ...

## Ограничения и контекст выполнения

- ...

## Краткое резюме

| метрика | значение |
|---|---|
| ошибки | <N> |
| предупреждения | <N> |
| информация | <N> |

## Группы проблем

| группа | количество | критичность |
|---|---|---|
| ... | ... | ... |

## Замечания

| код (code) | критичность (severity) | тип объекта (object_type) | объект (object_ref) | правило (rule) | подтверждение (evidence) | рекомендация (recommended_action) |
|---|---|---|---|---|---|---|
| ... | ... | ... | ... | ... | ... | ... |

## Подтверждение команд

| команда (command) | код выхода (exit_code) | краткий итог (summary) |
|---|---|---|
| ... | ... | ... |

## Топ-5 действий

1. ...
2. ...
3. ...
4. ...
5. ...

## Следующие действия

1. ...
```

## JSON Template (Required)

```json
{
  "report_version": "dbspec-report/v1",
  "report_type": "migration_health",
  "generated_at": "2026-02-19T00:00:00Z",
  "project_root": ".",
  "tooling": "binary",
  "status": "warning",
  "score": 72,
  "what_was_checked": [
    "dbspec migrations status",
    "dbspec migrations current",
    "dbspec migrations pending",
    "dbspec migrations history"
  ],
  "criteria_used": [
    "Команды миграций должны завершаться без ошибок",
    "Состояние должно быть synced для статуса ok"
  ],
  "execution_context": [
    "Локальный запуск",
    "Ограничения sandbox отсутствуют"
  ],
  "counts": {
    "error": 1,
    "warning": 2,
    "info": 1
  },
  "issue_groups": [
    {
      "group": "migration-command-failures",
      "count": 3,
      "max_severity": "error"
    }
  ],
  "findings": [
    {
      "code": "DBS-ENV-001",
      "severity": "error",
      "object_type": "workflow",
      "object_ref": "dbspec migrations history",
      "rule": "required-command-exit-code",
      "evidence": "Команда завершилась с кодом 1",
      "recommended_action": "Проверить окружение и доступ к БД"
    }
  ],
  "command_evidence": [
    {
      "command": "dbspec migrations status",
      "exit_code": 0,
      "summary": "Status: synced"
    }
  ],
  "top_actions": [
    "Исправить причины падения required команд",
    "Повторно запустить миграционный отчет"
  ],
  "next_actions": [
    "Запустить /dbspec-report-full после устранения ошибок"
  ]
}
```
