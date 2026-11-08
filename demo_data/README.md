# demo_data

Демонстрационные данные учебного проекта **Solar World**.

| Файл | Что это | Зачем здесь |
|---|---|---|
| `data.json` | Фикстура Django (`loaddata`) | Исходный набор данных для наполнения базы PostgreSQL |

## Почему это лежит в репозитории

Это осознанное упрощение для учебного проекта: после клонирования достаточно
создать базу, применить миграции и загрузить фикстуру одной командой.
В файле только демонстрационные записи — планет, спутников, миссий,
агентств, компаний и товаров магазина.

**В коммерческом проекте так не делают:** база не хранится в git,
а создаётся миграциями, демо-данные загружаются из фикстуры или
отдельного сида, а рабочая база живёт на сервере.

## Как используется

Проект работает только с PostgreSQL. Параметры подключения задаются
переменными `DB_*` в `.env` (или через `DATABASE_URL`). База должна быть
создана заранее, миграции — применены:

```bash
python manage.py migrate
python manage.py loaddata demo_data/data.json \
  -e contenttypes -e auth.permission -e admin.logentry -e sessions
```

Служебные таблицы Django (`contenttypes`, `auth.permission`, `admin.logentry`,
`sessions`) создаются миграциями, поэтому из фикстуры они исключены.
Файл `data.json` хранится в **UTF-8 без BOM**: `loaddata` не умеет читать
UTF-16 и падает с `UnicodeDecodeError`.

## Как обновить

После изменения данных в рабочей базе:

```bash
python manage.py dumpdata --natural-foreign --natural-primary \
  -e contenttypes -e auth.Permission -e sessions -e admin.logentry \
  -o demo_data/data.json --indent 2
```
