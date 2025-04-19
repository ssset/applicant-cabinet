# applications/urls.py
from django.urls import path
from .views import (
    ApplicationView, AvailableSpecialtiesView,
    ModeratorApplicationsView, ModeratorApplicationDetailView,
    LeaderboardView, AvailableOrganizationsView
)

urlpatterns = [
    path('applications/', ApplicationView.as_view(), name='applications'),
    path('available-specialties/', AvailableSpecialtiesView.as_view(), name='available_specialties'),
    path('available-organizations/', AvailableOrganizationsView.as_view(), name='available-organizations'),
    path('moderator/applications/', ModeratorApplicationsView.as_view(), name='moderator_applications'),
    path('moderator/application-detail/', ModeratorApplicationDetailView.as_view(), name='moderator_application_detail'),
    path('leaderboard/', LeaderboardView.as_view(), name='leaderboard'),
]