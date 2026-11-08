from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Пользователь проекта.

    Отдельная модель нужна, чтобы поля пользователя можно было расширять
    без замены встроенной модели Django.
    """

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
