#!/bin/bash
cd "$(dirname "$0")" || exit

echo "Enter commit message:"
read -r COMMIT_MSG

if [ -z "$COMMIT_MSG" ]; then
    echo "��������� �� ����� ���� ������. �����."
    exit 1
fi

git add .
git commit -m "$COMMIT_MSG"
git push
echo "������."