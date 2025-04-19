# static/urls.py
from django.urls import path
from .views import (
    ApplicationStatsView, SpecialtyStatsView, ActivityStatsView,
    ModeratorActivityStatsView, SystemStatsView, InstitutionStatsView,
    AdminActivityStatsView
)

urlpatterns = [
    path('applications/', ApplicationStatsView.as_view(), name='application_stats'),
    path('specialties/', SpecialtyStatsView.as_view(), name='specialty_stats'),
    path('activity/', ActivityStatsView.as_view(), name='activity_stats'),
    path('moderator-activity/', ModeratorActivityStatsView.as_view(), name='moderator_activity_stats'),
    path('system/', SystemStatsView.as_view(), name='system_stats'),
    path('institutions/', InstitutionStatsView.as_view(), name='institution_stats'),
    path('admin-activity/', AdminActivityStatsView.as_view(), name='admin_activity_stats'),
]