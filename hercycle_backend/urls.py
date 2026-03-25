
from django.contrib import admin
from django.urls import include, path

from api.views import user_spa_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('api/v1/', include('api.urls')),
    path('user/', user_spa_view, name='user_app_spa'),
]
