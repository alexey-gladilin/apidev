# Процесс Релиза APIDev

Статус: `Guide`

Документ описывает единый операционный процесс релиза standalone-бинарников `apidev` через GitHub Release workflow без неявных шагов.

## Область действия

- workflow: `.github/workflows/release.yml`;
- целевые платформы: `ubuntu-latest`, `macos-latest`, `windows-latest`;
- публикация: GitHub Release assets и workflow artifacts.

## Роли

- `Maintainer`: инициирует релиз, контролирует quality gates, подтверждает результат.
- `GitHub Actions`: собирает, smoke-проверяет, пакует и публикует артефакты.

## Предварительные условия

Перед релизом maintainer должен убедиться, что:

1. Все запланированные изменения для версии уже смержены в default branch.
2. Локально проходит минимум: `make docs-check`.
3. Версия согласована и выбрана в semver-формате (`vX.Y.Z`).
4. Есть права на создание GitHub Release в репозитории.

## Гигиена секретов (обязательно)

Для всех сценариев релиза действуют обязательные правила:

1. Не выводить секреты в логи CI/CD и локальные команды релиза.
2. Не включать токены/ключи/секретные значения в release notes, имена файлов и release assets.
3. Использовать токены по принципу least privilege: минимально необходимые scopes, ограниченный repository/environment, отдельный токен под конкретный publish-path.
4. Не использовать персональные долгоживущие токены, если доступен более безопасный механизм (например, `GITHUB_TOKEN` или короткоживущий service token с ограничениями).

Нарушение любого пункта блокирует завершение релиза до устранения риска.

## Security/Reproducibility Guardrails (обязательно)

Для release pipeline действуют дополнительные governance-требования:

1. Все GitHub Actions в `.github/workflows/release.yml` должны быть pinned на immutable full-length commit SHA (`owner/action@<40-hex-sha>`); использование floating refs (`@v*`, `@main`, `@master`) запрещено.
2. Для workflow и каждой release-job должны быть явные `permissions`; broad/default permissions без явного контракта запрещены.
3. Job `release` использует только минимально необходимый доступ для upload assets (`contents: write`), остальные job не должны расширять доступ без документированной причины.
4. `actions/checkout` должен работать без сохранения credentials (`persist-credentials: false`), чтобы исключить неявное распространение токена в последующие shell-steps.
5. Зависимости release-сборки должны быть детерминированы: lock-файл (`requirements/code.txt`) и pin critical tooling (например, `pyinstaller==...`) являются обязательными.

Нарушение любого пункта считается security/reproducibility regression и блокирует релиз до исправления workflow и документации.

## Основной сценарий (рекомендуемый)

### Шаг 1. Подготовить release tag и release notes

1. Выберите новую версию, например `v0.4.0`.
2. Подготовьте release notes.
3. Создайте GitHub Release с tag `v0.4.0` и статусом `published`.

Это действие автоматически запускает workflow `release` по событию `release.published`.

### Шаг 2. Дождаться прохождения quality gates в CI

В run workflow maintainer должен проверить, что job `release` успешно прошла для всех элементов matrix:

- `baseline-release-ubuntu-latest`
- `baseline-release-macos-latest`
- `baseline-release-windows-latest`

Обязательные quality gates внутри каждой matrix-задачи:

1. `Build standalone binary`
2. `Smoke check standalone binary`
3. `Resolve release version`
4. `Package standalone binary`
5. `Verify packaged artifact naming inventory`
6. `Upload packaged workflow artifact`
7. `Upload packaged GitHub Release asset`

Если любой gate падает, релиз считается незавершенным и требует исправления с новым повторным запуском через новый tag/release.

### Шаг 3. Проверить опубликованные артефакты

На странице релиза проверьте наличие одного артефакта на каждую платформу. Имена должны соответствовать паттерну:

- `apidev-<version>-<os>-<arch>.zip`
- `apidev-<version>-<os>-<arch>.tar.gz`

Минимальная проверка:

1. В названии всех файлов одинаковая версия `<version>`.
2. Для каждой целевой ОС присутствует ровно один архив.
3. Нет файлов, не соответствующих `apidev-<version>-<os>-<arch>`.

## Ручной запуск workflow_dispatch (только fallback)

Ручной запуск допустим для служебных сценариев (например, проверка пайплайна), но для production release должен использоваться запуск через `release.published`.

Если нужен `workflow_dispatch`:

1. Обязательно передавайте input `release_version` в формате `X.Y.Z` или `vX.Y.Z`.
2. Pipeline выполняет fail-fast pre-check: при пустом/пробельном `release_version` run останавливается до сборки и упаковки.
3. Для `workflow_dispatch` версия берется только из input `release_version` (fallback на `github.ref_name` отсутствует).
4. Для `release.published` источник версии остается прежним: `github.event.release.tag_name`.

## Инциденты и восстановление

Если публикация завершилась частично или с ошибкой:

1. Зафиксируйте упавший quality gate и причину.
2. Не редактируйте существующий релиз вручную до выяснения причины.
3. Подготовьте исправление в коде/скриптах/workflow.
4. Повторите процесс с новым tag/release.

Если обнаружена утечка секрета (в логах, release notes, asset, issue, комментарии):

1. Немедленно остановите дальнейшие релизные действия.
2. Отзовите (revoke) скомпрометированный токен и выполните ротацию секрета.
3. Удалите утекшее значение из публичных материалов (release notes/assets/log excerpts, где это возможно) и зафиксируйте факт инцидента.
4. Проверьте blast radius: какие репозитории/пакеты/интеграции были доступны по этому секрету.
5. Возобновляйте релиз только после подтвержденной ротации и повторной проверки прав доступа по least privilege.

## Связанные документы

- `docs/process/release-checklist.md`
- `docs/process/testing-strategy.md`
- `docs/README.md`
