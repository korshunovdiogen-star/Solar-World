"""Одноразовый переход со встроенной auth.User на accounts.User.

Django не позволяет менять AUTH_USER_MODEL на базе, где уже применены
миграции: запись admin.0001_initial оказывается «старше» своей новой
зависимости accounts.0001_initial, и migrate падает с
InconsistentMigrationHistory.

Команда решает это без потери данных: таблицы auth_user* переименовываются
в accounts_user* (структура у моделей одинаковая), а миграция
accounts.0001_initial отмечается применённой. Дальше обычный migrate
работает как обычно. На новой базе команда ничего не делает.
"""

from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.db.migrations.recorder import MigrationRecorder

APP_LABEL = "accounts"
MIGRATION_NAME = "0001_initial"

# Порядок важен: сначала основная таблица, потом связующие.
TABLE_RENAMES = (
    ("auth_user", "accounts_user"),
    ("auth_user_groups", "accounts_user_groups"),
    ("auth_user_user_permissions", "accounts_user_user_permissions"),
)


class Command(BaseCommand):
    help = "Переносит пользователей из auth_user в accounts_user (старая база)."

    def handle(self, *args, **options):
        recorder = MigrationRecorder(connection)
        already_applied = (APP_LABEL, MIGRATION_NAME) in recorder.applied_migrations()

        if already_applied:
            self.stdout.write("Модель accounts.User уже используется, перенос не нужен.")
            return

        if not recorder.has_table():
            # Совсем чистая база: обычный migrate создаст всё с нуля.
            self.stdout.write("База пустая, перенос не нужен.")
            return

        tables = set(connection.introspection.table_names())
        quote = connection.ops.quote_name

        if "accounts_user" in tables:
            # Таблица уже создана, но запись о миграции потерялась.
            # Достаточно отметить миграцию применённой.
            recorder.record_applied(APP_LABEL, MIGRATION_NAME)
            self.stdout.write(
                self.style.SUCCESS("Таблица accounts_user уже есть, миграция отмечена применённой.")
            )
            return

        old_tables = [old for old, _ in TABLE_RENAMES if old in tables]
        if not old_tables:
            self.stdout.write("Таблиц auth_user нет, перенос не нужен.")
            return

        with transaction.atomic():
            with connection.cursor() as cursor:
                for old_name, new_name in TABLE_RENAMES:
                    if old_name in tables and new_name not in tables:
                        cursor.execute(f"ALTER TABLE {quote(old_name)} RENAME TO {quote(new_name)}")
                        self.stdout.write(f"  {old_name} -> {new_name}")

            recorder.record_applied(APP_LABEL, MIGRATION_NAME)

        self.stdout.write(
            self.style.SUCCESS(
                "Пользователи перенесены в accounts_user, миграция отмечена применённой."
            )
        )
