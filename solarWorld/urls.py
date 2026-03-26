from django.contrib import admin
from django.urls import path
from planets import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.main, name='main'),
    path('planets/', views.planet_list, name='planet_list'),
    path('planet/<int:pk>/', views.planet_detail, name='planet_detail'),
    path('satellite/<int:pk>/', views.satellite_detail, name='satellite_detail'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)