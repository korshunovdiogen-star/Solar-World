from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from .models import Favorite, History
from django.http import Http404, JsonResponse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
import json


def _get_content_type(content_type):
    """Находит ContentType модели из приложения planets."""
    return get_object_or_404(
        ContentType,
        app_label='planets',
        model=content_type.lower(),
    )


def _get_favorite_target(content_type, object_id):
    """Проверяет, что тип и объект существуют, и возвращает ContentType."""
    content_type_obj = _get_content_type(content_type)
    model = content_type_obj.model_class()
    if model is None:
        raise Http404('Неизвестная модель')
    get_object_or_404(model, pk=object_id)
    return content_type_obj


def _safe_redirect(request):
    """Возвращает назад, но только на страницу этого же сайта."""
    referer = request.META.get('HTTP_REFERER', '')
    if referer and url_has_allowed_host_and_scheme(
        referer,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(referer)
    return redirect('main')

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # автоматический вход после регистрации
            return redirect('main')  # перенаправление на главную
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
@require_POST
def add_favorite(request, content_type, object_id):
    content_type_obj = _get_favorite_target(content_type, object_id)
    Favorite.objects.get_or_create(
        user=request.user,
        content_type=content_type_obj,
        object_id=object_id
    )
    # Перенаправляет обратно на страницу, с которой пришли
    return _safe_redirect(request)

@login_required
@require_POST
def remove_favorite(request, content_type, object_id):
    content_type_obj = _get_favorite_target(content_type, object_id)
    Favorite.objects.filter(
        user=request.user,
        content_type=content_type_obj,
        object_id=object_id
    ).delete()
    return _safe_redirect(request)

@login_required
def profile(request):
    favorites = Favorite.objects.filter(user=request.user).select_related('content_type')
    history = History.objects.filter(user=request.user).select_related('content_type')[:20] 
    context = {
        'favorites': favorites,
        'history': history,
    }
    return render(request, 'users/profile.html', context)





@login_required
@require_POST
def toggle_favorite(request):
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    if not isinstance(data, dict):
        return JsonResponse({'error': 'Invalid data'}, status=400)

    content_type = data.get('content_type')
    object_id = data.get('object_id')

    if not isinstance(content_type, str) or not content_type or object_id is None:
        return JsonResponse({'error': 'Missing data'}, status=400)

    try:
        object_id = int(object_id)
    except (TypeError, ValueError):
        return JsonResponse({'error': 'Invalid object id'}, status=400)

    try:
        content_type_obj = _get_favorite_target(content_type, object_id)
    except Http404:
        return JsonResponse({'error': 'Object not found'}, status=404)

    favorite, created = Favorite.objects.get_or_create(
        user=request.user,
        content_type=content_type_obj,
        object_id=object_id
    )
    if not created:
        favorite.delete()
        is_favorite = False
    else:
        is_favorite = True
    return JsonResponse({'is_favorite': is_favorite})