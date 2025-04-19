# users/urls.py
from django.urls import path
from .views import ApplicantProfileView, AdminAppCreationView, AdminOrgView, ModeratorView, CurrentUserView

urlpatterns = [
    path('profile/', ApplicantProfileView.as_view(), name='applicant-profile'),
    path('admin-app/create/', AdminAppCreationView.as_view(), name='admin-app-create'),
    path('admin-org/', AdminOrgView.as_view(), name='admin-org'),
    path('admin-org/<int:id>/', AdminOrgView.as_view(), name='admin-org-detail'),  # Новый маршрут для DELETE
    path('moderators/', ModeratorView.as_view(), name='moderators'),
    path('me/', CurrentUserView.as_view(), name='current-user'),
]