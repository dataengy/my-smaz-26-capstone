[EN](COMMANDS.md) | [RU](COMMANDS.ru.md)

# Справка по командам

Makefile — точка входа для обычной локальной работы. Он использует `uv` и по умолчанию помещает окружение и кэш проекта в `.run/venv` и `.run/uv-cache`. Сначала установите [uv](https://docs.astral.sh/uv/) и Python версии 3.11 или новее, затем один раз выполните `make setup`, чтобы установить зависимости разработки из lock-файла. Запускайте команды из корня проекта. Для установки нужен доступ к package index, если зависимости ещё не кэшированы.

```sh
make help
make setup
make download       # нужен доступ к сети; загружает настроенные источники
make features       # строит аналитическую таблицу по локальным снимкам
make run            # офлайн-процесс исследования; нужны загруженные снимки
make run-notebook   # запускает Jupyter для notebooks/workflow.ipynb
make demo-synthetic # генерирует синтетические входы и визуальный HTML-отчёт
make test-demo-synthetic # проверяет офлайн human-demo
make test
make test-unit
make test-integration
make test-smoke
make e2e-origin     # опционально; нужна CAPSTONE_E2E_ORIGIN
make e2e-real       # опционально; нужна CAPSTONE_E2E_CONFIG
make hooks
make install-hooks
make periodic-install  # необязательное расписание macOS; подробности в инструкции
make usage          # экспериментальная сводка локальных метаданных Codex
```

`make download` обращается к внешним поставщикам и может перезаписать локальные снимки источников. Снимки и результаты хранятся в игнорируемых Git каталогах `data/` и `artifacts/`. E2E-тесты включаются явно; необходимые переменные окружения описаны в [инструкции запуска](RUNBOOK.ru.md). Сводка `usage` не является полной историей сессий или отчётом о расходах.

## Диагностика сети и чистая установка

Используйте эти скрипты, если доступ к источникам или установка зависимостей вызывают сомнения:

```sh
python3 scripts/check_external_access.py
python3 scripts/check_external_access.py --only yahoo_gld_5d_chart
python3 scripts/check_external_access.py --only cftc_disaggregated_futures_only_gold_api
python3 scripts/check_clean_install.py
```

Проверка источников записывает результаты DNS и ограниченных HTTPS-запросов к GitHub, PyPI, CFTC, Yahoo Finance, FRED, Stooq и Alpha Vantage. Она читает не более 8 КиБ ответа, проверяет форму данных CFTC/Yahoo/CSV, не сохраняет рыночные данные и не повторяет HTTP 429. Если `urllib` получает таймаут на главной странице FRED, скрипт выполняет ограниченный запрос через `curl`, отбрасывает тело и отдельно записывает HTTP-код и IP сервера. Это помогает отличить проблему клиента/CDN-узла от недоступности хоста; доступ к API FRED и пригодность данных с точки зрения point-in-time этим не проверяются. Запрос к Stooq ограничен коротким недавним дневным срезом GLD. Опцию `--only` можно указать несколько раз для выбора отдельных endpoint; `--timeout` задаёт таймаут запроса. Запускайте проверку в той же сетевой среде, где выполняется загрузка. Запрет DNS-сокетов в sandbox сам по себе не доказывает общий DNS-сбой устройства. Скрипт чистой установки использует `uv.lock` и extra `dev` во временном окружении с новым временным uv-кешем, проверяет импорты, поддержку формата ноутбука и сессию XNYS, затем удаляет временное окружение и кеш. Он не запускает тесты и не загружает рыночные снимки проекта.

Синтетическое демо генерирует детерминированные фиктивные ряды рынка и COT, после чего запускает настоящий код построения признаков, выбора модели и симуляции. Внешние источники не вызываются, а метрики не являются исследовательскими результатами. После `make demo-synthetic` откройте `artifacts/synthetic-demo/index.html`; подробности — в [описании human-demo](SYNTHETIC_DEMO.ru.md).

В Justfile находятся вспомогательные, многошаговые и агентские операции. Для них установите [just](https://just.systems/):

```sh
just --list
just doctor
just lock-check
just compile
just verify-fast
just verify
just prompt-check <lock-slug> <session-id>
just prompt-take <lock-slug> <session-id> "<reason>"
just prompt-release <lock-slug> <session-id>
just take-next-prompt <session-id>
```

`just verify` проверяет инструменты, lock-файл в офлайн-режиме, компиляцию и полный набор тестов. `just verify-fast` запускает компиляцию и unit-, integration- и smoke-тесты. Операции сессий используют локальные advisory-блокировки объектов; срок их действия автоматически не истекает. Перед работой проверьте владельца и снимайте только собственную блокировку. Команды `make doctor`, `make verify`, `make verify-fast` и `make agents` являются делегатами Just и требуют установленного Just.

Например, переменные окружения можно переопределить так:

```sh
UV_PROJECT_ENVIRONMENT=.run/venv UV_CACHE_DIR=.run/uv-cache make test
UV_PROJECT_ENVIRONMENT=.run/venv UV_CACHE_DIR=.run/uv-cache just verify
```

Настройка источников и офлайн-повтор описаны в [инструкции запуска](RUNBOOK.ru.md), границы этапов — в [архитектуре](ARCHITECTURE.ru.md).

Интервал можно изменить командой `make periodic-install PERIODIC_INTERVAL_MINUTES=60`. Цели `periodic-uninstall` и `periodic-run` удаляют расписание или запускают один цикл. См. [инструкцию по периодическому коммиту и push](PERIODIC_COMMIT_PUSH.ru.md) с описанием ограничений и поведения.
