#!/bin/bash
PROJECT_DIR="/c/django/DjangoProjects/solarWorld"
FASTAPI_DIR="$PROJECT_DIR/fastapi_random_planets"
cd "$PROJECT_DIR" || exit
cleanup() {
    kill $FASTAPI_PID 2>/dev/null
    kill $DJANGO_PID 2>/dev/null
    exit
}
trap cleanup SIGINT SIGTERM
cd "$FASTAPI_DIR" || exit
uvicorn main:app --reload --port 8001 &
FASTAPI_PID=$!
sleep 2
cd "$PROJECT_DIR" || exit
python manage.py runserver &
DJANGO_PID=$!
wait