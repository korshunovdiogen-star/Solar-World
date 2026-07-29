#!/bin/bash
echo "Enter commit message:"
read -r COMMIT_MSG

if [ -z "$COMMIT_MSG" ]; then
    echo "Сообщение не может быть пустым. Выход."
    exit 1
fi

git add .
git commit -m "$COMMIT_MSG"
git push
echo "Готово."