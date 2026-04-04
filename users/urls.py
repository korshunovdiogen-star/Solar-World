from django.urls import path
from . import views

urlpatterns = [
    path('favorite/add/<str:content_type>/<int:object_id>/', views.add_favorite, name='add_favorite'),
    path('favorite/remove/<str:content_type>/<int:object_id>/', views.remove_favorite, name='remove_favorite'),
    path('profile/', views.profile, name='profile'),
    path('favorite/toggle/', views.toggle_favorite, name='toggle_favorite'),
]