from django.urls import path
from .views import RegisterView, VerifyEmailView, ApplicantProfileView, AdminAppCreationView, OrganizationView, AdminOrgCreationView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('verify/', VerifyEmailView.as_view(), name='verify_email'),
    path('admin-app/create/', AdminAppCreationView.as_view(), name='admin_app_create'),
    path('organizations/', OrganizationView.as_view(), name='organizations'),
    path('admin-org/create/', AdminOrgCreationView.as_view(), name='admin_org_create'),
]