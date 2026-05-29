#!/bin/bash
# ---------------------------------------------
# Скрипт для локального развёртывания
# ---------------------------------------------

echo ">>> 1. Создаётся виртуальное окружение, если его нет..."
if [ ! -d "venv" ]; then
    python -m venv venv
    echo "Окружение создано."
else
    echo "Окружение уже существует."
fi

echo ">>> 2. Активируется виртуальное окружение..."
source venv/Scripts/activate

echo ">>> 3. Устанавливаются зависимости..."
pip install -r requirements.txt

echo ">>> 4. Применяются миграции..."
python manage.py migrate

echo ">>> 5. Загружаются тестовые данные..."
if [ -f "data.json" ]; then
    python manage.py loaddata data.json
    echo "Данные загружены."
else
    echo "Файл data.json не найден – пропускаю загрузку данных."
fi

echo ">>> 6. Запускается сервер разработки..."
echo "Сайт будет доступен по адресу http://127.0.0.1:8000"
python manage.py runserver