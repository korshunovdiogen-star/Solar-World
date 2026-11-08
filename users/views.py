import json

from django.contrib import admin
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.prefetch import GenericPrefetch
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from planets.models import Company, Mission, Planet, Satellite, SpaceAgency

from .forms import RegisterForm, RemainingAttemptsAuthenticationForm
from .models import Favorite, History
from .rate_limit import (
    LOGIN_IP_LIMIT,
    LOGIN_USER_LIMIT,
    LOGIN_WINDOW_SECONDS,
    get_client_ip,
    get_count,
    is_limited,
    register_failure,
    reset,
)


def _get_content_type(content_type):
    """Находит ContentType модели из приложения planets."""
    return get_object_or_404(
        ContentType,
        app_label="planets",
        model=content_type.lower(),
    )


def _get_favorite_target(content_type, object_id):
    """Проверяет, что тип и объект существуют, и возвращает ContentType."""
    content_type_obj = _get_content_type(content_type)
    model = content_type_obj.model_class()
    if model is None:
        raise Http404("Неизвестная модель")
    get_object_or_404(model, pk=object_id)
    return content_type_obj


def _with_generic_objects(queryset):
    """Подгружает избранное и историю пачкой: один запрос на каждую модель.

    Без этого шаблон профиля обращается к content_object у каждой записи,
    и Django делает отдельный запрос на каждую строку (N+1).
    """
    return queryset.prefetch_related(
        GenericPrefetch(
            "content_object",
            [
                Planet.objects.all(),
                Satellite.objects.all(),
                Mission.objects.all(),
                SpaceAgency.objects.all(),
                Company.objects.all(),
            ],
        )
    )


def _safe_redirect(request):
    """Возвращает назад, но только на страницу этого же сайта."""
    referer = request.META.get("HTTP_REFERER", "")
    if referer and url_has_allowed_host_and_scheme(
        referer,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(referer)
    return redirect("main")


def _login_keys(request):
    """Возвращает IP посетителя и ключ «IP + логин» для счётчиков."""
    username = request.POST.get("username", "").strip()
    ip = get_client_ip(request)
    user_key = f"{ip}|{username.lower()}" if username else None
    return ip, user_key


def _is_login_limited(ip, user_key):
    """True, если хотя бы один из лимитов уже исчерпан."""
    return is_limited("login-ip", ip, LOGIN_IP_LIMIT) or bool(
        user_key and is_limited("login-ip-user", user_key, LOGIN_USER_LIMIT)
    )


def _register_login_failure(ip, user_key):
    """Считает одну неудачную попытку по IP и по паре «IP + логин»."""
    register_failure("login-ip", ip)
    if user_key:
        register_failure("login-ip-user", user_key)


def _reset_login_failures(ip, user_key):
    """Сбрасывает оба счётчика после успешного входа."""
    reset("login-ip", ip)
    if user_key:
        reset("login-ip-user", user_key)


def _too_many_attempts_message():
    wait_minutes = LOGIN_WINDOW_SECONDS // 60
    return (
        "Слишком много неудачных попыток входа. "
        f"Подождите {wait_minutes} минут и попробуйте снова."
    )


class RateLimitedLoginView(LoginView):
    """
    Обычная страница входа Django, но с защитой от подбора пароля.

    Неудачные попытки считаются по IP и по паре «IP + логин».
    После каждой неудачи форма показывает, сколько попыток осталось.
    """

    authentication_form = RemainingAttemptsAuthenticationForm

    def post(self, request, *args, **kwargs):
        ip, user_key = _login_keys(request)

        if _is_login_limited(ip, user_key):
            form = self.get_form()
            form.add_error(None, _too_many_attempts_message())
            response = self.render_to_response(
                self.get_context_data(form=form),
                status=429,
            )
            response["Retry-After"] = str(LOGIN_WINDOW_SECONDS)
            return response

        return super().post(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        if self.request.method == "POST":
            kwargs["remaining"] = self._remaining_attempts()

        return kwargs

    def form_invalid(self, form):
        ip, user_key = _login_keys(self.request)
        _register_login_failure(ip, user_key)
        return super().form_invalid(form)

    def form_valid(self, form):
        ip, user_key = _login_keys(self.request)
        _reset_login_failures(ip, user_key)
        return super().form_valid(form)

    def _remaining_attempts(self):
        ip, user_key = _login_keys(self.request)

        ip_remaining = LOGIN_IP_LIMIT - (get_count("login-ip", ip) + 1)
        if user_key:
            user_remaining = LOGIN_USER_LIMIT - (get_count("login-ip-user", user_key) + 1)
        else:
            user_remaining = ip_remaining

        # Показываем меньший остаток: именно он закончится первым.
        return max(0, min(ip_remaining, user_remaining))


def rate_limited_admin_login(request, extra_context=None):
    """
    Вход в админку с той же защитой от подбора пароля, что и обычный вход.

    Админка использует собственный шаблон и форму, поэтому здесь мы
    оборачиваем её стандартное представление, а не создаём своё.
    """
    if request.method == "POST":
        ip, user_key = _login_keys(request)

        if _is_login_limited(ip, user_key):
            # Показываем обычную страницу входа админки, но без проверки пароля.
            original_method = request.method
            request.method = "GET"
            try:
                response = admin.site.login(request, extra_context)
            finally:
                request.method = original_method

            if hasattr(response, "context_data"):
                form = response.context_data["form"]
                # Форма не привязана к данным (мы показываем её как GET),
                # поэтому Django не создал cleaned_data. Для add_error он нужен.
                form.cleaned_data = {}
                form.add_error(None, _too_many_attempts_message())
            response.status_code = 429
            response["Retry-After"] = str(LOGIN_WINDOW_SECONDS)
            return response

    response = admin.site.login(request, extra_context)

    if request.method == "POST":
        ip, user_key = _login_keys(request)
        # Успешный вход в админку делает пользователя staff-пользователем.
        # Обычный пользователь, который уже вошёл на сайт, не должен
        # сбрасывать счётчики неудачных попыток входа в админку.
        if request.user.is_authenticated and request.user.is_staff:
            _reset_login_failures(ip, user_key)
        else:
            _register_login_failure(ip, user_key)

    return response


def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # автоматический вход после регистрации
            return redirect("main")  # перенаправление на главную
    else:
        form = RegisterForm()
    return render(request, "registration/register.html", {"form": form})


@login_required
@require_POST
def add_favorite(request, content_type, object_id):
    content_type_obj = _get_favorite_target(content_type, object_id)
    Favorite.objects.get_or_create(
        user=request.user, content_type=content_type_obj, object_id=object_id
    )
    # Перенаправляет обратно на страницу, с которой пришли
    return _safe_redirect(request)


@login_required
@require_POST
def remove_favorite(request, content_type, object_id):
    content_type_obj = _get_favorite_target(content_type, object_id)
    Favorite.objects.filter(
        user=request.user, content_type=content_type_obj, object_id=object_id
    ).delete()
    return _safe_redirect(request)


@login_required
def profile(request):
    favorites = _with_generic_objects(
        Favorite.objects.filter(user=request.user).select_related("content_type")
    )
    history = _with_generic_objects(
        History.objects.filter(user=request.user).select_related("content_type")
    )[:20]
    context = {
        "favorites": favorites,
        "history": history,
    }
    return render(request, "users/profile.html", context)


@login_required
@require_POST
def toggle_favorite(request):
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    if not isinstance(data, dict):
        return JsonResponse({"error": "Invalid data"}, status=400)

    content_type = data.get("content_type")
    object_id = data.get("object_id")

    if not isinstance(content_type, str) or not content_type or object_id is None:
        return JsonResponse({"error": "Missing data"}, status=400)

    try:
        object_id = int(object_id)
    except (TypeError, ValueError):
        return JsonResponse({"error": "Invalid object id"}, status=400)

    try:
        content_type_obj = _get_favorite_target(content_type, object_id)
    except Http404:
        return JsonResponse({"error": "Object not found"}, status=404)

    favorite, created = Favorite.objects.get_or_create(
        user=request.user, content_type=content_type_obj, object_id=object_id
    )
    if not created:
        favorite.delete()
        is_favorite = False
    else:
        is_favorite = True
    return JsonResponse({"is_favorite": is_favorite})
