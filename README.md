# Solar World – Космическая энциклопедия

[![Django CI](https://github.com/korshunovdiogen-star/Solar-World/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/korshunovdiogen-star/Solar-World/actions/workflows/ci.yml)

**Solar World** — интерактивная энциклопедия о космосе: карта Солнечной системы, каталог объектов, личный кабинет и микросервис «Планета дня».

**Сайт:** [https://solar-world.alwaysdata.net](https://solar-world.alwaysdata.net) (работает без VPN)

## Кратко

**Что это.** Учебный проект на Django: статьи о планетах, спутниках, миссиях, агентствах и компаниях, интерактивная карта, поиск, фильтры и сортировка. Отдельный микросервис на FastAPI выбирает «планету дня» для главной страницы. Раздел магазина пока в разработке.

**Как пользоваться.** Откройте сайт: карта — на главной, полный список объектов — в «Каталоге». Регистрация нужна только для избранного, история просмотров сохраняется автоматически. Админка — `/admin/`, документация микросервиса — `/fastapi/docs`.

**Запуск локально.** `scripts\setup.bat`, затем `scripts\start.bat` → http://127.0.0.1:8000. Подробнее — в разделе [Установка и запуск](#установка-и-запуск).

**Статус.** Тесты и деплой автоматизированы через GitHub Actions: push в `main` проходит тесты и, если они зелёные, автоматически выкатывается на хостинг.

## Оглавление

1. [Кратко](#кратко)
2. [Описание](#описание)
3. [Возможности](#возможности)
4. [Скриншоты](#скриншоты)
5. [Технологии](#технологии)
6. [Установка и запуск](#установка-и-запуск)
7. [Переменные окружения](#переменные-окружения)
8. [API](#api)
9. [Структура проекта](#структура-проекта)
10. [Тестирование](#тестирование)
11. [Деплой](#деплой)
12. [Известные проблемы](#известные-проблемы-и-ограничения)
13. [Планы](#планы)
14. [Автор](#автор)

## Описание

**Solar World** — это интерактивная веб-энциклопедия, посвящённая космосу. Сайт позволяет изучать планеты, спутники, космические миссии, агентства и частные компании. Ключевые особенности:

- Интерактивная карта Солнечной системы с всплывающими подсказками.
- Каталог с поиском, фильтрацией по категориям, сортировкой и пагинацией.
- Личный кабинет: избранное и история просмотров.
- Sci‑fi дизайн, анимации, звуковые эффекты.
- **🌠 Планета дня** – на главной странице отображается планета, выбранная с помощью микросервиса на FastAPI.
- **🛒 Магазин** – раздел находится в разработке.

Проект развёрнут на бесплатном хостинге alwaysdata и доступен без VPN:  
[https://solar-world.alwaysdata.net](https://solar-world.alwaysdata.net)

## Возможности

- **Главная страница** – Приветственная страница проекта с направлениями к интерактивной карте или каталогу.
- **🌍 Интерактивная карта Солнечной системы** – кликабельные зоны планет с всплывающими подсказками.
- **📚 Обширная энциклопедия** – подробные статьи о планетах, спутниках, космических миссиях, агентствах и частных компаниях.
- **🔍 Каталог** – поиск по названию, фильтрация по 5 категориям (планеты, спутники, миссии, агентства, компании), сортировка по различным полям (название, радиус, тип, прибыль, страна и др.), пагинация.
- **👤 Личный кабинет** – регистрация, вход, управление избранным и историей (без регистрации доступен весь базовый функционал).
- **⭐ Избранное** – авторизованные пользователи могут добавлять понравившиеся объекты в личный список избранного.
- **📜 История просмотров** – автоматически сохраняются последние просмотренные статьи (до 20 записей).
- **🌠 Планета дня** – каждый день на главной странице показывается одна планета, вычисленная на основе SHA-256 от даты (через микросервис FastAPI). Карточка содержит название, изображение, первую строку описания и ведёт на детальную страницу. Миниатюра для карточки уменьшается один раз в сутки и кешируется в Redis до полуночи, поэтому полноразмерный файл на главную не загружается.
- **🎨 Sci‑Fi дизайн** – неоновая подсветка, анимированные уголки, эффект стекла, адаптивная вёрстка.
- **🔊 Звуковые эффекты** – приятный звук при наведении на кнопки (работает после первого клика на странице).
- **⚡ Быстрая загрузка** – локальные шрифты (Goblin One, Orbitron) без внешних CDN, сжатый фон, Debug Toolbar отключён по умолчанию.
- **⚙️ API** – эндпоинт `/api/catalog/` для поиска, фильтрации и сортировки объектов. API построено на Generic Views и Serializers Django REST Framework; поиск, фильтрация по категориям, сортировка и пагинация выполняются его штатными средствами.
- **🛒 Магазин** – раздел в разработке: страница доступна по адресу `/shop/`, но функциональность пока не готова.
- **🚀 Живой проект** – сайт развёрнут на бесплатном хостинге alwaysdata и доступен по ссылке без VPN.

## Скриншоты

### Главная страница

![Главная страница](screenshots/%D0%93%D0%BB%D0%B0%D0%B2%D0%BD%D0%B0%D1%8F.PNG)

### Каталог

![Каталог](screenshots/%D0%9A%D0%B0%D1%82%D0%B0%D0%BB%D0%BE%D0%B3.PNG)

### Детальная страница планеты

![Детальная страница](screenshots/%D0%94%D0%B5%D1%82%D0%B0%D0%BB%D1%8C%D0%BD%D0%B0%D1%8F%20%D1%81%D1%82%D1%80%D0%B0%D0%BD%D0%B8%D1%86%D0%B0.PNG)

### Личный кабинет

![Личный кабинет](screenshots/%D0%9B%D0%B8%D1%87%D0%BD%D1%8B%D0%B9%20%D0%BA%D0%B0%D0%B1%D0%B8%D0%BD%D0%B5%D1%82.PNG)

### Интерактивная карта

![Интерактивная карта](screenshots/%D0%9A%D0%B0%D1%80%D1%82%D0%B0.PNG)

## Технологии

- **Backend**:
  - Python 3.12–3.14 (на сервере 3.12, локально проверено на 3.14.7)
  - Django 5.2.2
  - Django REST Framework 3.17.1
  - drf-spectacular 0.30.0 (OpenAPI/Swagger для DRF)
  - **Микросервис (Планета дня)**:
    - FastAPI
    - Uvicorn (локальный запуск)
    - a2wsgi (ASGI → WSGI, чтобы микросервис работал на хостинге)

- **Кеширование**:
  - Redis (django-redis)
  - Локально: Memurai или Redis в Docker
  - На хостинге: Aiven Valkey (бесплатный, совместим с Redis)

- **Frontend**:
  - HTML5
  - CSS3 (адаптивная вёрстка, CSS Grid, Flexbox, анимации)
  - JavaScript (ES6, fetch API, работа с DOM)
  - SVG (интерактивная карта)
  - Локальные шрифты Goblin One и Orbitron (`static/fonts`)

- **База данных**:
  - PostgreSQL (основная база для разработки и деплоя)
  - SQLite (запасной вариант и база для тестов)

- **Управление версиями и хостинг**:
  - Git
  - GitHub (репозиторий, CI/CD через GitHub Actions)
  - alwaysdata (бесплатный хостинг: Django + FastAPI + PostgreSQL)
  - Aiven (бесплатный Redis-совместимый Valkey)
  - Render (альтернатива, поддержка в настройках проекта)

- **Контейнеризация**:
  - Docker

- **Библиотеки и зависимости**:
  - Pillow – обработка изображений
  - python-dotenv – управление переменными окружения
  - requests – для взаимодействия с микросервисом (в Django)
  - redis, django-redis – кеширование
  - whitenoise, gunicorn – раздача статики и запуск в продакшене
  - psycopg2, dj-database-url – подключение к PostgreSQL
  - django-debug-toolbar – отладочная панель (включается по флагу)
  - sqlparse, tzdata – вспомогательные пакеты

- **Тестирование**:
  - pytest
  - pytest-django
  - coverage (измерение покрытия кода)
  - httpx (TestClient для FastAPI)
  - ruff, black (линтер и форматтер, проверяются в CI)

## Установка и запуск

### Быстрый запуск на Windows (рекомендуется)

В папке `scripts/` лежат готовые скрипты. Их можно запускать двойным кликом: окно не закрывается и ждёт нажатия клавиши. Логика находится в `scripts/_impl/*.ps1`, а `.bat` — тонкие обёртки для запуска из Проводника.

| Скрипт | Что делает |
|---|---|
| `setup.bat` | создаёт виртуальное окружение (`venv` или использует существующее `env`), устанавливает зависимости, создаёт `.env` с `SECRET_KEY`, применяет миграции, загружает демонстрационные данные |
| `start.bat` | проверяет порты и Redis, запускает FastAPI (порт 8001) и Django (порт 8000) |
| `start_tests.bat` | запускает тесты (pytest) |
| `git_push.bat` | делает коммит и отправляет изменения на GitHub (репозиторий запоминается) |

Порядок действий:

1. Запустить `scripts\setup.bat` (достаточно один раз).
2. Установить Redis-совместимый сервер (Memurai) и убедиться, что он работает на `127.0.0.1:6379`:

   ```powershell
   winget install -e --id Memurai.MemuraiDeveloper
   ```
3. Запустить `scripts\start.bat`.
4. Открыть в браузере: http://127.0.0.1:8000
5. Для проверки тестов запустить `scripts\start_tests.bat`.

Скрипты поддерживают параметры:

```bat
scripts\start.bat -DjangoPort 8080 -FastApiPort 8081
scripts\start_tests.bat -NoPause
```

`-NoPause` отключает ожидание клавиши (полезно для CI).

### Публикация изменений на GitHub

Скрипт `git_push.bat` делает коммит и отправляет изменения в удалённый репозиторий. Он не привязан к конкретному репозиторию: при первом запуске спрашивает путь к локальной папке git-репозитория или URL GitHub, а затем запоминает выбор.

1. Запустите `scripts\git_push.bat`.
2. В первый раз укажите папку репозитория (например, `C:\Projects\Solar-World`) или URL GitHub. Если папка ещё не является репозиторием, скрипт предложит выполнить `git init`; если указан URL — предложит клонировать его в выбранную папку. Если URL совпадает с текущим проектом (сравнение без учёта `.git` и регистра), скрипт просто использует текущую папку и ничего не клонирует.
3. Введите сообщение коммита. Пустое сообщение отменяет публикацию.
4. Скрипт выполнит `git add -A`, создаст коммит и отправит текущую ветку в `origin` (`git push -u origin <ветка>`).

Выбранный репозиторий сохраняется в `%APPDATA%\Solar-World\git-push.json`, поэтому при следующих запусках скрипт сразу работает с ним. Чтобы выбрать другой репозиторий, запустите с флагом `-Reset`.

Параметры:

```bat
scripts\git_push.bat -Reset
scripts\git_push.bat -Repo "C:\Projects\Solar-World" -Message "Обновил README"
scripts\git_push.bat -NoPause
```

- `-Repo` — путь или URL репозитория (можно указать сразу, без вопроса).
- `-Message` — сообщение коммита (без интерактивного ввода).
- `-Reset` — забыть сохранённый репозиторий и выбрать заново.
- `-NoPause` — не ждать нажатия клавиши.

Скрипт проверяет служебные файлы и папки (`venv`, `env`, `__pycache__`, `.pytest_cache`, `.coverage`, `media`): если они не покрыты `.gitignore` или уже отслеживаются, он предупредит, что они попадут в коммит. Если правило в `.gitignore` есть, но файлы уже в индексе, скрипт подскажет `git rm -r --cached`. `demo_data/` в этой проверке не участвует: демо-база и фикстура оставлены в репозитории осознанно. Для работы нужен установленный Git; если его нет в `PATH`, скрипт ищет стандартные пути установки.

### Ручной запуск (любая ОС)

Через командную строку.

**1. Клонировать репозиторий**

```bash
git clone https://github.com/korshunovdiogen-star/Solar-World.git
cd Solar-World
```

**2. Создать и активировать виртуальное окружение**

Windows:

```powershell
python -m venv venv
venv\Scripts\activate
```

macOS/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

**3. Установить зависимости**

```bash
pip install -r requirements.txt
```

**4. Запустить Redis**

Кеш проекта работает через Redis, поэтому без него сайт не запустится полностью (будут ошибки подключения к `127.0.0.1:6379`).

Варианты:

- Memurai (Windows): установить и запустить службу;
- Redis в Docker:

```bash
docker run -d --rm --name solar-world-redis -p 6379:6379 redis:7-alpine
```

**5. Создать файл `.env`**

Создайте `.env` в корне проекта (пример — в разделе [Переменные окружения](#переменные-окружения)).

**6. Применить миграции**

```bash
python manage.py migrate
```

**7. Загрузить демонстрационные данные**

```bash
python manage.py loaddata demo_data/data.json -e contenttypes -e auth.permission -e admin.logentry -e sessions
```

**8. Собрать статические файлы**

```bash
python manage.py collectstatic
```

**9. Создать суперпользователя (для доступа к админке)**

```bash
python manage.py createsuperuser
```

**10. Запустить сервер разработки**

```bash
python manage.py runserver
```

После этого откройте в браузере: http://127.0.0.1:8000

### Запуск микросервиса FastAPI (Планета дня)

Микросервис работает отдельно и должен быть запущен параллельно с Django.

1. Перейдите в папку микросервиса:

   ```bash
   cd fastapi_random_planets
   ```

2. Установите зависимости (если ещё не установлены):

   ```bash
   pip install -r ../requirements.txt
   ```

3. Запустите сервер FastAPI:

   ```bash
   uvicorn main:app --reload --port 8001
   ```

Теперь микросервис доступен по адресу http://127.0.0.1:8001.

Если FastAPI недоступен, главная страница продолжит работать, но карточка «Планета дня» не отобразится.

### Запуск с помощью Docker (альтернативный способ)

1. Убедитесь, что Docker установлен.
2. Клонируйте репозиторий и перейдите в папку проекта:

   ```bash
   git clone https://github.com/korshunovdiogen-star/Solar-World.git
   cd Solar-World
   ```

3. Соберите и запустите контейнеры:

   ```bash
   docker compose up --build
   ```

   В старых версиях Docker Compose команда называется `docker-compose up --build`.

Откройте в браузере: http://localhost:8000

`docker compose` поднимает PostgreSQL, Redis, Django и FastAPI. Django и FastAPI подключаются к PostgreSQL из этого же compose-файла. На Render адрес базы по-прежнему задаётся через `DATABASE_URL`.

### Примечания

- Для корректной работы карты, блока «Планета дня», кеша и звуковых эффектов убедитесь, что запущен Redis и собраны статические файлы (шаг 8).
- Если вы используете переменные окружения (файл `.env`), создайте его в корне проекта и пропишите необходимые параметры (например, `SECRET_KEY`). Пример:

  ```ini
  SECRET_KEY=ваш-секретный-ключ
  DEBUG=True
  ```

- Режим отладки `DEBUG` читается из `.env` или переменных окружения. Локально по умолчанию включён, в production (`ENVIRONMENT=prod`) автоматически выключается. Явное значение `DEBUG` имеет приоритет.
- Debug Toolbar по умолчанию выключен. Включить: `ENABLE_DEBUG_TOOLBAR=1` в `.env` или переменных окружения и перезапустить сервер.
- При возникновении ошибок проверьте, что все зависимости установлены, миграции применены, а Redis доступен.

## Переменные окружения

Для работы проекта необходимо задать следующие переменные окружения. Вы можете создать файл `.env` в корне проекта или установить их через системные переменные.

```ini
# Файл .env (пример)

SECRET_KEY=ваш-секретный-ключ
DEBUG=True
ENVIRONMENT=local
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=
USE_HTTPS=0
FASTAPI_URL=http://localhost:8001
REDIS_URL=redis://127.0.0.1:6379/1
ENABLE_DEBUG_TOOLBAR=0
```

- SECRET_KEY – секретный ключ Django (обязательно задайте свой, не используйте значение по умолчанию). Для локальной разработки можно сгенерировать новый на Djecrety.

- DEBUG – режим отладки. Локально по умолчанию `True`; в production (`ENVIRONMENT=prod` или запуск на Render/Railway/Heroku) автоматически `False`. Явное значение в `.env` или окружении имеет приоритет.

- ALLOWED_HOSTS – список доменов/IP через запятую. По умолчанию `localhost,127.0.0.1,[::1]`. На Render внешний домен (`RENDER_EXTERNAL_HOSTNAME`) добавляется автоматически. На другом хостинге укажите свой домен, например `example.com,www.example.com`.

- ENVIRONMENT – профиль окружения: `local` или `prod`. Влияет на `DEBUG`, HTTPS, адрес FastAPI и выбор настроек. Если переменная не задана, окружение определяется автоматически: Render/Railway/Heroku → `prod`, иначе `local`. На alwaysdata переменная задаётся явно: `ENVIRONMENT=prod`.

- CSRF_TRUSTED_ORIGINS – доверенные источники для CSRF через запятую, обязательно с протоколом: `https://example.com`. На Render домен добавляется автоматически.

- USE_HTTPS – включает HTTPS-редирект и secure-cookies. По умолчанию `True` в production и `False` локально; можно переопределить вручную.

- SECURE_HSTS_SECONDS – срок HSTS в секундах (в production по умолчанию `3600`).

- FASTAPI_URL – адрес микросервиса FastAPI. По умолчанию `http://localhost:8001`.

- REDIS_URL – адрес Redis для кеша. По умолчанию `redis://127.0.0.1:6379/1`.

- ENABLE_DEBUG_TOOLBAR – включает Debug Toolbar (`1`, `true`, `yes`, `on`). По умолчанию выключен.

- DB_ENGINE, DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT – параметры подключения к PostgreSQL. Если `DB_ENGINE` не задан, Django и FastAPI используют SQLite из `demo_data/db.sqlite3`.

> **Важно:** файл `.env` не должен попадать в репозиторий. Добавьте его в `.gitignore`.

## API

Проект предоставляет REST API для получения объектов каталога с возможностью поиска, фильтрации, сортировки и пагинации.

### Документация API

| Что | Адрес |
|---|---|
| Swagger UI (DRF) | [https://solar-world.alwaysdata.net/api/docs/](https://solar-world.alwaysdata.net/api/docs/) |
| OpenAPI-схема (JSON) | [https://solar-world.alwaysdata.net/api/schema/?format=json](https://solar-world.alwaysdata.net/api/schema/?format=json) |
| Swagger UI (FastAPI) | [https://solar-world.alwaysdata.net/fastapi/docs](https://solar-world.alwaysdata.net/fastapi/docs) |

Swagger показывает эндпоинты моделей (`/api/planets/`, `/api/satellites/`, `/api/missions/`, `/api/agencies/`, `/api/companies/`). Основной эндпоинт каталога `/api/catalog/` описан ниже.

### Эндпоинт: `/api/catalog/`

**Метод:** `GET`

**Параметры запроса (все необязательные):**

| Параметр    | Тип    | Описание                                                                 |
|-------------|--------|--------------------------------------------------------------------------|
| `q`         | string | Поисковый запрос (по названию объекта).                                   |
| `category`  | string | Категория: `planet`, `satellite`, `mission`, `agency`, `company`, `all` (по умолчанию). |
| `ordering`  | string | Поле сортировки с направлением. Возможные значения: `name_asc`, `name_desc`, `radius_asc`, `radius_desc`, `type_asc`, `type_desc`, `mission_type_asc`, `mission_type_desc`, `agency_asc`, `agency_desc`, `revenue_asc`, `revenue_desc`, `country_asc`, `country_desc`. |
| `page`      | int    | Номер страницы (пагинация, по умолчанию 12 объектов на страницу).         |

**Пример запроса:**

```http
GET /api/catalog/?q=марс&category=planet&ordering=radius_desc&page=2
```

**Пример ответа (JSON):**

```json
{
  "results": [
    {
      "id": 4,
      "name": "Марс",
      "model_type": "planet",
      "type_display": "Планета земной группы",
      "radius": 3390,
      "image": "/media/planets/mars.jpg",
      "first_line": "Красная планета с самой высокой горой",
      ...
    }
  ],
  "total_pages": 5,
  "current_page": 2
}
```

### Служебные эндпоинты «Планеты дня»

| Эндпоинт | Назначение |
|---|---|
| `/planet-of-the-day/` | перенаправляет на детальную страницу планеты, выбранной на сегодня |
| `/planet-of-the-day/thumbnail/` | отдаёт уменьшенную WebP-миниатюру (128×128) для карточки на главной; генерируется один раз в сутки и кешируется в Redis до полуночи |

### Примечания

- Если категория не указана, возвращаются объекты всех типов.
- Сортировка по имени (`name_asc` / `name_desc`) — единственная, доступная для всех категорий. Остальные варианты доступны индивидуально для каждой категории.
- Пагинация фиксированная — 12 объектов на страницу.
- Ответ `/api/catalog/` кешируется на 15 минут (в том числе по параметрам запроса).

## Структура проекта

Основные каталоги и файлы:

- `planets/` – основное приложение: модели (планеты, спутники, миссии, агентства, компании), представления, сериализаторы, API, админка.
- `users/` – приложение для аутентификации и работы с профилями, избранным и историей.
- `shop/` – приложение магазина (в разработке).
- `templates/` – HTML-шаблоны (базовый, каталог, детальные страницы, регистрация/вход и т.д.).
- `static/` – статические файлы (CSS, JavaScript, изображения, звуки, иконки, локальные шрифты в `static/fonts`).
- `media/` – демонстрационные и пользовательские медиафайлы (картинки планет, логотипы компаний и агентств). Папка хранится в git, чтобы демо работало сразу после клонирования.
- `scripts/` – скрипты для Windows: `setup.bat`, `start.bat`, `start_tests.bat`, `git_push.bat` и реализация в `scripts/_impl/*.ps1`.
- `manage.py` – скрипт управления Django (миграции, запуск сервера, shell и т.д.).
- `requirements.txt` – зависимости для запуска, `requirements-dev.txt` – pytest, coverage, линтеры и другие инструменты разработки.
- `demo_data/` – демонстрационная база SQLite (`db.sqlite3`) и фикстура `data.json` для `loaddata`. Подробнее – в `demo_data/README.md`.
- `pytest.ini` – настройки pytest.
- `pyproject.toml` – настройки ruff и black (линтер и форматтер).
- `.env` (опционально) – переменные окружения (секретный ключ, режим отладки и т.п.).
- `solarWorld/` (или `название_проекта/`) – папка с общепроектными настройками (`settings.py`, `urls.py`, `wsgi.py`).
- `fastapi_random_planets/` – микросервис на FastAPI для генерации планеты дня; `wsgi.py` – точка входа для запуска под WSGI на хостинге.
- `screenshots/` – скриншоты для README.
- `Dockerfile.django`, `Dockerfile.fastapi`, `docker-compose.yml` – контейнеризация проекта.
- `.github/workflows/ci.yml` – CI/CD: тесты на каждый push и автодеплой на alwaysdata после успешных тестов в `main`.

## Тестирование

Проект покрыт unit-тестами и интеграционными тестами с использованием `pytest` и `pytest-django`. Основные тесты проверяют:

- Модели (`Planet`, `Satellite`, `Mission`, `SpaceAgency`, `Company`, а также модели пользователей, избранного и истории).
- API каталога (поиск, фильтрация, сортировка, пагинация).
- Представления (views) для планет, спутников, миссий, агентств, компаний, а также регистрацию, вход, профиль, избранное и историю.

**Количество тестов:** 134  
**Общее покрытие кода тестами:** 88% (на 6 ноября 2026 г.)

**Как запустить тесты:**

```bash
pytest
```

В Windows также можно запустить `scripts\start_tests.bat`.

**Измерить покрытие:**

```bash
coverage run --source='.' -m pytest
coverage report
coverage html
```

**Примечание:** для тестов и линта нужны dev-зависимости (`pytest`, `pytest-django`, `coverage`, `httpx`, `ruff`, `black`):

```bash
pip install -r requirements-dev.txt
```

## Деплой

Сайт развёрнут на бесплатном хостинге **alwaysdata** и открывается без VPN:

**URL:** [https://solar-world.alwaysdata.net](https://solar-world.alwaysdata.net)

### Схема

| Компонент | Где работает |
|---|---|
| Django (основной сайт) | alwaysdata, сайт типа **Python WSGI**, адрес `solar-world.alwaysdata.net` |
| FastAPI («Планета дня») | alwaysdata, второй сайт **Python WSGI**, адрес `solar-world.alwaysdata.net/fastapi` |
| PostgreSQL | alwaysdata |
| Redis | Aiven, бесплатный Valkey (совместим с Redis) |
| Статика | WhiteNoise, Django сам раздаёт `/static/` |
| Медиа | Django раздаёт `/media/` в production |

Код на сервере — `~/solar-world`, виртуальное окружение — `~/venv` (Python 3.12), файл `.env` лежит рядом с кодом и в git не попадает.

### CI/CD (GitHub Actions)

Workflow: `.github/workflows/ci.yml`.

**CI — на каждый push и pull request:**
1. `ruff check .` и `black --check .`;
2. `python manage.py check`;
3. миграции на PostgreSQL;
4. `pytest` — 134 теста.

**CD — автоматический деплой после зелёных тестов в ветке `main`:**
1. обновляет код на сервере по SSH;
2. ставит зависимости из `requirements.txt`;
3. применяет миграции;
4. собирает статику (`collectstatic`);
5. перезапускает сайты Django и FastAPI через API alwaysdata.

Если тесты упали, деплой не запускается и сайт остаётся на предыдущей версии.

Деплой включается переменной репозитория `ENABLE_DEPLOY=true`:

```text
Settings → Secrets and variables → Actions → Variables
```

Секреты репозитория:

| Секрет | Назначение |
|---|---|
| `ALWAYSDATA_SSH_KEY_B64` | приватный SSH-ключ в base64 (одной строкой) |
| `ALWAYSDATA_SSH_HOST` | `ssh-solar-world.alwaysdata.net` |
| `ALWAYSDATA_SSH_USER` | `solar-world` |
| `ALWAYSDATA_API_KEY` | токен alwaysdata API |
| `ALWAYSDATA_ACCOUNT` | `solar-world` |
| `ALWAYSDATA_DJANGO_SITE_ID` | ID сайта Django |
| `ALWAYSDATA_FASTAPI_SITE_ID` | ID сайта FastAPI |

`ALWAYSDATA_KNOWN_HOSTS` необязателен: если его нет, ключ хоста определяется автоматически на раннере.

Запустить деплой вручную: `Actions → Django CI → Run workflow`.

### Первичная настройка сервера (один раз)

1. Клонировать репозиторий и создать окружение:

```bash
git clone https://github.com/korshunovdiogen-star/Solar-World.git ~/solar-world
python3.12 -m venv ~/venv
~/venv/bin/pip install -r ~/solar-world/requirements.txt
```

2. Создать `~/solar-world/.env` (пример ниже).

3. Создать два сайта типа **Python WSGI**:

| Поле | Django | FastAPI |
|---|---|---|
| Addresses | `solar-world.alwaysdata.net` | `solar-world.alwaysdata.net/fastapi` |
| Application path | `~/solar-world/solarWorld/wsgi.py` | `~/solar-world/fastapi_random_planets/wsgi.py` |
| Working directory | `~/solar-world` | `~/solar-world/fastapi_random_planets` |
| Virtualenv | `~/venv` | `~/venv` |
| Python version | 3.12 | 3.12 |

4. Выполнить первичные команды:

```bash
cd ~/solar-world && source ~/venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py loaddata demo_data/data.json -e contenttypes -e auth.permission -e admin.logentry -e sessions -e auth.user -e users
```

5. Перезапустить оба сайта в панели.

### Пример `.env` на сервере

```ini
ENVIRONMENT=prod
DEBUG=False
ALLOWED_HOSTS=solar-world.alwaysdata.net
CSRF_TRUSTED_ORIGINS=https://solar-world.alwaysdata.net
FASTAPI_URL=https://solar-world.alwaysdata.net/fastapi
SECRET_KEY=ваш-секретный-ключ
```

### Обновление данных и кеша

Каталог кешируется на 15 минут. После `loaddata` или правки объектов кеш нужно очистить:

```bash
cd ~/solar-world && source ~/venv/bin/activate
python manage.py shell -c "from django.core.cache import cache; cache.clear(); print('cache cleared')"
```

### Альтернативные варианты

- **Docker** – `docker-compose up --build` поднимает Django, FastAPI, PostgreSQL и Redis.
- **Render** – окружение определяется автоматически по переменной `RENDER`: включаются `DEBUG=False`, HTTPS-редирект и secure-cookies, `RENDER_EXTERNAL_HOSTNAME` добавляется в `ALLOWED_HOSTS` и `CSRF_TRUSTED_ORIGINS`, база подключается через `DATABASE_URL`, статика раздаётся через WhiteNoise.

## Известные проблемы и ограничения

- **Магазин в разработке** – раздел `/shop/` пока не готов к использованию.
- **Redis обязателен** – без Redis кеш недоступен; в тестах автоматически используется `DummyCache`.
- **Первый запрос после простоя** – на бесплатном тарифе alwaysdata приложение останавливается после 30 минут без запросов, поэтому первый запрос может открываться на несколько секунд дольше.
- **SQLite – запасной вариант** – подходит для тестов и простого запуска, но не для параллельной работы. Рабочая база проекта – PostgreSQL.
- **Демонстрационная БД в репозитории** – файлы `demo_data/db.sqlite3` и `demo_data/data.json` коммитятся вместе с проектом, чтобы после клонирования сайт сразу запускался с готовыми данными. Это сознательное упрощение для учебного проекта; в реальном проекте базу в репозиторий не добавляют.
- **Медиафайлы** – папка `media/` с демонстрационными изображениями хранится в репозитории (около 28 МБ), чтобы сайт работал сразу после клонирования. Файлы, загруженные через админку непосредственно на сервере, остаются только там: в git они не попадают, и деплой их не переносит.

## Планы

- Завершить разработку магазина (`shop/`)
- Добавить смену пароля и восстановление доступа
- Предлагать регистрацию при попытке добавить объект в избранное
- Возвращать пользователя к верху страницы при перелистывании каталога

## Автор

**Коршунов Егор Евгеньевич**  
**GitHub:** [@korshunovdiogen-star](https://github.com/korshunovdiogen-star)  
**Год:** 2026
