@echo off
if not exist venv (
    python -m venv venv
)
call venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
if exist data.json python manage.py loaddata data.json
python manage.py runserver
pause