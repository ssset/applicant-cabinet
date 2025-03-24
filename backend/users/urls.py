
from django.urls import path
from .views import ApplicantProfileView, AdminAppCreationView, AdminOrgCreationView, ModeratorView

urlpatterns = [
    path('profile/', ApplicantProfileView.as_view(), name='applicant_profile'),
    path('admin-app/create/', AdminAppCreationView.as_view(), name='admin_app_create'),
    path('admin-org/create/', AdminOrgCreationView.as_view(), name='admin_org_create'),
    path('moderators/', ModeratorView.as_view(), name='moderators'),
]