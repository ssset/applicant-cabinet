# applicant/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('auth_app.urls')),
    path('api/users/', include('users.urls')),
    path('api/org/', include('org.urls')),
    path('api/applications/', include('applications.urls')),
]