from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError

User = get_user_model()


class RegisterForm(UserCreationForm):
    """Форма регистрации для текущей модели пользователя.

    Стандартная UserCreationForm жёстко привязана к auth.User и падает,
    когда AUTH_USER_MODEL указывает на accounts.User.
    """

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username",)


class RemainingAttemptsAuthenticationForm(AuthenticationForm):
    """
    Форма входа, которая после неудачи пишет, сколько попыток осталось.

    Число попыток передаёт страница входа, сама форма ничего не считает.
    """

    def __init__(self, *args, remaining=None, **kwargs):
        self.remaining = remaining
        super().__init__(*args, **kwargs)

    def get_invalid_login_error(self):
        if self.remaining is None:
            return super().get_invalid_login_error()

        return ValidationError(
            "Неверный логин или пароль. Осталось попыток: %(remaining)s.",
            code="invalid_login",
            params={
                "username": self.username_field.verbose_name,
                "remaining": self.remaining,
            },
        )
