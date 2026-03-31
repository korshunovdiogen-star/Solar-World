from django.urls import path, include
from rest_framework.routers import DefaultRouter
from planets.views import PlanetViewSet, SatelliteViewSet, MissionViewSet, SpaceAgencyViewSet
from django.contrib import admin
from planets import views
from django.conf import settings
from django.conf.urls.static import static

# API
router = DefaultRouter()
router.register(r'planets', PlanetViewSet)
router.register(r'satellites', SatelliteViewSet)
router.register(r'missions', MissionViewSet)
router.register(r'agencies', SpaceAgencyViewSet)
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.main, name='main'),
    path('planets/', views.planet_list, name='planet_list'),
    path('planet/<int:pk>/', views.planet_detail, name='planet_detail'),
    path('satellite/<int:pk>/', views.satellite_detail, name='satellite_detail'),
    path('mission/<int:pk>/', views.mission_detail, name='mission_detail'),
    path('spaceAgency/<int:pk>/', views.spaceAgency_detail, name='spaceAgency_detail'),
    path('api/', include(router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



