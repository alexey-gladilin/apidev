# Чеклист Релиза APIDev

Статус: `Guide`

Документ фиксирует обязательные шаги релиза и явные quality gates, которые maintainer должен проверить перед завершением публикации.

## Чеклист перед запуском

- [ ] Версия выбрана в формате `vX.Y.Z`.
- [ ] Подготовлены release notes.
- [ ] Для docs-среза выполнено: `make docs-check`.
- [ ] Подтверждено, что релиз запускается через GitHub Release (`published`), а не из произвольной ветки.
- [ ] Проверено, что release notes не содержат токены/ключи/секреты и ссылки на приватные секретные данные.
- [ ] Подтверждено, что для publish используются только токены с минимально необходимыми scopes (least privilege).

## Чеклист гигиены секретов (обязательно)

- [ ] В release-скриптах и командах отключен вывод секретов в лог (`set -x` и эквиваленты не должны печатать токены).
- [ ] Секреты не попадают в имена release assets, содержимое архивов и метаданные публикации.
- [ ] Для каждого secret-required шага используется отдельный токен с ограничением по репозиторию/окружению и минимальным TTL (если применимо).
- [ ] Не используются персональные долгоживущие токены без документированного исключения.

## Security/Reproducibility Review Checklist (обязательно)

- [ ] Все `uses:` в `.github/workflows/release.yml` pinned на immutable `@<40-hex-sha>` (без `@v*`, `@main`, `@master`).
- [ ] В workflow задан top-level `permissions`, и у всех release jobs (`release`, `publish-homebrew`) заданы explicit `permissions`.
- [ ] `release` job ограничен минимально необходимым доступом для публикации assets (`contents: write`), без дополнительных scopes.
- [ ] `actions/checkout` запускается с `persist-credentials: false` и не оставляет токен в git-config шагов после checkout.
- [ ] Release build использует детерминированные зависимости (`requirements/code.txt` + pinned tooling, включая `pyinstaller==...`).
- [ ] Изменения в security/reproducibility guardrails подтверждены контрактными тестами release workflow.

## Чеклист запуска

- [ ] Создан GitHub Release с нужным tag `vX.Y.Z`.
- [ ] Release переведен в статус `published`.
- [ ] Автоматически стартовал workflow `.github/workflows/release.yml`.
- [ ] Для `workflow_dispatch` обязательно задан input `release_version` (`X.Y.Z` или `vX.Y.Z`); пустое значение блокирует run до build/package.

## Quality Gates (обязательно)

Каждый gate должен быть `passed` для всех matrix-платформ (`ubuntu-latest`, `macos-latest`, `windows-latest`).

| Gate | Где проверяется | Критерий прохождения |
|---|---|---|
| Pre-check manual version input | Step `Pre-check workflow_dispatch version input` | Для `workflow_dispatch`: input `release_version` непустой после нормализации |
| Сборка бинарника | Step `Build standalone binary` | PyInstaller-сборка завершается без ошибок |
| Smoke-проверка | Step `Smoke check standalone binary` | Команда `apidev --help` выполняется успешно |
| Разрешение версии | Step `Resolve release version` | `release_version` не пустой |
| Упаковка | Step `Package standalone binary` | Создан архив в `dist/release` |
| Детерминированный нейминг | Step `Verify packaged artifact naming inventory` | Ровно 1 архив на платформу и паттерн `apidev-<version>-<os>-<arch>` |
| Публикация workflow artifact | Step `Upload packaged workflow artifact` | Артефакт доступен в GitHub Actions run |
| Публикация release asset | Step `Upload packaged GitHub Release asset` | Артефакт появился на странице GitHub Release |

## Чеклист после публикации

- [ ] На странице GitHub Release есть артефакты для всех 3 ОС.
- [ ] Имена всех артефактов соответствуют `apidev-<version>-<os>-<arch>`.
- [ ] Нет лишних/дублирующихся файлов для одной платформы.
- [ ] Release notes соответствуют фактической версии и содержимому релиза.

## Fail Policy

- Любой провал quality gate блокирует завершение релиза.
- Не допускается считать релиз успешным при green только части matrix.
- После исправления причин сбоя релиз повторяется новым tag/release.
- Любой признак утечки секрета блокирует релиз до revoke+rotation и повторной security-проверки.

## Incident Response (утечка секрета)

- [ ] Немедленно остановлены релизные действия и зафиксирован канал утечки.
- [ ] Выполнены revoke и rotation скомпрометированного секрета.
- [ ] Утекший секрет удален из release notes/assets/логов (где возможно) и задокументирован инцидент.
- [ ] Проверен blast radius и подтвержден возврат к least-privilege доступам перед перезапуском релиза.

## Проверяемые команды и артефакты

- Локальная документационная проверка: `make docs-check`.
- CI workflow: `.github/workflows/release.yml`.
- Артефакты публикации: GitHub Release assets + workflow artifacts.

## Связанные документы

- `docs/process/release-process.md`
- `docs/process/testing-strategy.md`
- `docs/README.md`
