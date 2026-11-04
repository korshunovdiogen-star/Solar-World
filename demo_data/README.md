# demo_data

Демонстрационные данные учебного проекта **Solar World**.

| Файл | Что это | Зачем здесь |
|---|---|---|
| `db.sqlite3` | Готовая база SQLite со всеми записями | Чтобы после клонирования сайт запускался без настройки PostgreSQL |
| `data.json` | Фикстура Django (`loaddata`) | Исходный набор данных для наполнения любой базы |

## Почему это лежит в репозитории

Это осознанное упрощение для учебного проекта: нужен запуск «из коробки»,
без отдельного шага с получением дампа или настройкой внешней базы.
В файлах только демонстрационные записи — планет, спутников, миссий,
агентств, компаний и товаров магазина.

**В коммерческом проекте так не делают:** база не хранится в git,
а создаётся миграциями, демо-данные загружаются из фикстуры или
отдельного сида, а рабочая база живёт на сервере.

## Как используется

- **PostgreSQL (основной режим).** Задайте `DB_ENGINE=django.db.backends.postgresql`
  и параметры `DB_*` в `.env`. Файлы отсюда не нужны, кроме `data.json`
  для первичного наполнения:

  ```bash
  python manage.py loaddata demo_data/data.json \
    -e contenttypes -e auth.permission -e admin.logentry -e sessions
  ```

  Служебные таблицы Django (`contenttypes`, `auth.permission`, `admin.logentry`,
  `sessions`) создаются миграциями, поэтому из фикстуры они исключены.
  Файл `data.json` хранится в **UTF-8 без BOM**: `loaddata` не умеет читать
  UTF-16 и падает с `UnicodeDecodeError`.

- **SQLite (запасной режим).** Не задавайте `DB_ENGINE` — Django возьмёт
  `demo_data/db.sqlite3`. Тот же файл читает микросервис FastAPI,
  поэтому путь задан в двух местах и должен совпадать:
  `solarWorld/settings.py` (`SQLITE_DB_PATH`) и
  `fastapi_random_planets/database.py` (`SQLITE_URL`).

## Как обновить

После изменения данных в рабочей базе:

```bash
# PostgreSQL -> фикстура
python manage.py dumpdata --natural-foreign --natural-primary \
  -e contenttypes -e auth.Permission -e sessions -e admin.logentry \
  -o demo_data/data.json --indent 2

# SQLite -> готовый файл
python manage.py dumpdata ... # либо просто скопировать актуальный db.sqlite3
```
