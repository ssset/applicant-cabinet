from django.urls import path
from .views import ApplicationView, AvailableSpecialtiesView

urlpatterns = [
    path('applications/', ApplicationView.as_view(), name='applications'),
    path('available-specialties/', AvailableSpecialtiesView.as_view(), name='available_specialties'),
]