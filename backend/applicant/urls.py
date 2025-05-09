from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from users.views import TaskStatusView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('auth_app.urls')),
    path('api/users/', include('users.urls')),
    path('api/org/', include('org.urls')),
    path('api/applications/', include('applications.urls')),
    path('api/message/', include('message.urls')),
    path('api/statistics/', include('static.urls')),
    path('task-status/', TaskStatusView.as_view(), name='task-status'),
    path('api/users/task-status/', TaskStatusView.as_view(), name='task-status'),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)