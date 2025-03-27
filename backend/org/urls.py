
from django.urls import path
from .views import OrganizationView, BuildingView, SpecialtyView, BuildingSpecialtyView

urlpatterns = [
    path('organizations/', OrganizationView.as_view(), name='organizations'),
    path('buildings/', BuildingView.as_view(), name='buildings'),
    path('specialties/', SpecialtyView.as_view(), name='specialties'),
    path('building-specialties/', BuildingSpecialtyView.as_view(), name='building_specialties'),
]
