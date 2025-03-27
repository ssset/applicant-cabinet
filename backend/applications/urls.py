# applications/urls.py
from django.urls import path
from .views import ApplicationView, AvailableSpecialtiesView, ModeratorApplicationsView, ModeratorApplicationDetailView

urlpatterns = [
    path('applications/', ApplicationView.as_view(), name='applications'),
    path('available-specialties/', AvailableSpecialtiesView.as_view(), name='available_specialties'),
    path('moderator/applications/', ModeratorApplicationsView.as_view(), name='moderator_applications'),
    path('moderator/application-detail/', ModeratorApplicationDetailView.as_view(), name='moderator_application_detail'),
]