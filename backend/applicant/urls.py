from django.contrib import admin
from django.urls import path
from auth_app.views import RegisterView, VerifyEmailView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/register/', RegisterView.as_view(), name='register'),
    path('api/auth/verify/', VerifyEmailView.as_view(), name='verify_email'),
    path('api/profile/', ApplicantProfileView.as_view(), name='applicant_profile'),
]
