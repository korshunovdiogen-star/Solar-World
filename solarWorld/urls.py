from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter
from planets.views import PlanetViewSet, SatelliteViewSet, MissionViewSet, SpaceAgencyViewSet, CompanyViewSet, company_detail
from django.contrib import admin
from planets import views
from users import views as user_views
from shop import views as shop_views
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve


# API
router = DefaultRouter()
router.register(r'planets', PlanetViewSet)
router.register(r'satellites', SatelliteViewSet)
router.register(r'missions', MissionViewSet)
router.register(r'agencies', SpaceAgencyViewSet)
router.register(r'companies', CompanyViewSet)
urlpatterns = [
    path('admin/login/', user_views.rate_limited_admin_login),
    path('admin/', admin.site.urls),
    path('', views.main, name='main'),
    path('planet-of-the-day/', views.planet_of_the_day, name='planet_of_the_day'),
    path('planet-of-the-day/thumbnail/', views.planet_of_the_day_thumbnail, name='planet_of_the_day_thumbnail'),
    path('planets/', views.planet_list, name='planet_list'),
    path('planet/<int:pk>/', views.planet_detail, name='planet_detail'),
    path('satellite/<int:pk>/', views.satellite_detail, name='satellite_detail'),
    path('mission/<int:pk>/', views.mission_detail, name='mission_detail'),
    path('spaceAgency/<int:pk>/', views.spaceAgency_detail, name='spaceagency_detail'),
    path('company/<int:pk>/', company_detail, name='company_detail'),
    path('api/', include(router.urls)),
    path('catalog/', views.catalog_page, name='catalog'),
    path('api/catalog/', views.catalog_api, name='catalog_api'),
    path('accounts/login/', user_views.RateLimitedLoginView.as_view(), name='login'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('register/', user_views.register, name='register'),
    path('users/', include('users.urls')),
    path('profile/', user_views.profile, name='profile'),
    path('shop/', include('shop.urls')),
]

# if settings.DEBUG:
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    if getattr(settings, 'ENABLE_DEBUG_TOOLBAR', False):
        import debug_toolbar
        urlpatterns = [
            re_path(r'^__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # В продакшене DEBUG выключен, поэтому static() ничего не добавляет.
    # На alwaysdata и в Docker медиа-файлы отдаёт сама Django: отдельного
    # веб-сервера для /media/ там нет.
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    ]


