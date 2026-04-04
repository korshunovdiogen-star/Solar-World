from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from .models import Favorite, History
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

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
def add_favorite(request, content_type, object_id):
    """Добавляет объект в избранное"""
    content_type_obj = get_object_or_404(ContentType, app_label='planets', model=content_type)
    favorite, created = Favorite.objects.get_or_create(
        user=request.user,
        content_type=content_type_obj,
        object_id=object_id
    )
    # Перенаправляем обратно на страницу, с которой пришли
    return redirect(request.META.get('HTTP_REFERER', 'main'))

@login_required
def remove_favorite(request, content_type, object_id):
    """Удаляет объект из избранного"""
    content_type_obj = get_object_or_404(ContentType, app_label='planets', model=content_type)
    Favorite.objects.filter(
        user=request.user,
        content_type=content_type_obj,
        object_id=object_id
    ).delete()
    return redirect(request.META.get('HTTP_REFERER', 'main'))

@login_required
def profile(request):
    favorites = Favorite.objects.filter(user=request.user).select_related('content_type')
    history = History.objects.filter(user=request.user).select_related('content_type')[:20]  # последние 20
    context = {
        'favorites': favorites,
        'history': history,
    }
    return render(request, 'users/profile.html', context)





@login_required
@csrf_exempt
def toggle_favorite(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        content_type = data.get('content_type')   # 'planet', 'satellite', 'mission', 'spaceagency'
        object_id = data.get('object_id')
        if not content_type or not object_id:
            return JsonResponse({'error': 'Missing data'}, status=400)
        try:
            ct = ContentType.objects.get(model=content_type, app_label='planets')
        except ContentType.DoesNotExist:
            return JsonResponse({'error': 'Invalid content type'}, status=400)
        favorite, created = Favorite.objects.get_or_create(
            user=request.user,
            content_type=ct,
            object_id=object_id
        )
        if not created:
            favorite.delete()
            is_favorite = False
        else:
            is_favorite = True
        return JsonResponse({'is_favorite': is_favorite})
    return JsonResponse({'error': 'Method not allowed'}, status=405)