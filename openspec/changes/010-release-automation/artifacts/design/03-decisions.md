# Decisions and Trade-offs

## D1. GitHub Actions как основной release orchestration слой
- Решение: реализовать release automation через `.github/workflows` с trigger `release: published` и `workflow_dispatch`.
- Причина: репозиторный, прозрачный и auditable процесс без внешнего оркестратора.
- Альтернативы:
  - external CI/CD platform;
  - локальный скриптовый release.
- Почему отклонены: выше операционная стоимость и слабее traceability в рамках репозитория.

## D2. Matrix build по `macOS|Windows|Linux` как базовый обязательный контур
- Решение: core pipeline строится на matrix jobs для трех ОС.
- Причина: explicit соответствие spec requirement для multi-OS binary delivery.
- Альтернативы:
  - сначала single-OS publish, затем эволюция;
  - поэтапное подключение платформ.
- Почему отклонены: не покрывают требуемый release contract Horizon 2.

## D3. Smoke gate обязателен перед publish
- Решение: `apidev --help` выполняется как обязательный gate до упаковки/публикации assets.
- Причина: минимальная гарантия runnable бинарника и снижение риска broken release.
- Альтернативы:
  - только build success без runtime smoke;
  - расширенный smoke suite на старте.
- Компромисс: выбран минимальный smoke как баланс скорости и надежности, расширение возможно в следующей фазе.

## D4. Детерминированный naming contract для артефактов
- Решение: canonical формат `apidev-<version>-<os>-<arch>`.
- Причина: предсказуемый download/install UX и машинная обработка release inventory.
- Альтернативы:
  - свободное именование по job/runner;
  - naming без явного `arch`.
- Почему отклонены: усложняют поддержку и повышают риск коллизий/неоднозначности.

## D5. Homebrew publish как отдельный secret-gated path
- Решение: Homebrew publish выполняется отдельной job с обязательной проверкой секрета.
- Причина: изоляция рисков внешнего publish path от core GitHub release assets.
- Альтернативы:
  - встроить Homebrew steps в основной publish job;
  - исключить Homebrew из первой итерации.
- Компромисс: путь остается optional, но архитектурно подготовлен и контролируем.

## D6. Документация release flow как часть definition of done
- Решение: включить обновление `README` (Distribution) и process checklist в обязательный scope.
- Причина: без явной документации автоматизация остается непрозрачной для maintainers и пользователей.
- Альтернативы:
  - ограничиться только CI workflow без документации.
- Почему отклонено: рост bus factor и ошибок ручного сопровождения релизов.

## Assumptions
- Maintainers управляют релизами через GitHub Releases, а не через отдельный private deployment pipeline.
- Репозиторий имеет достаточные права/секреты для публикации assets и (опционально) Homebrew formula.
- Release artifact naming contract не конфликтует с существующими внешними интеграциями.

## Risks
- Секреты и permissions могут отличаться между организациями/форками и ломать Homebrew path.
- Изменение release формата в будущем может потребовать migration в документации и tooling.
- Недостаточная observability pipeline затруднит triage редких межплатформенных падений.

## Open Questions
- Должен ли Homebrew path быть soft-fail (warning) или hard-fail для всего release процесса?
- Нужно ли фиксировать SLA по длительности release pipeline для maintainers?
- Нужна ли автоматическая подпись/проверка checksum assets в первой итерации или это отдельный change?
