
from django.urls import path
from .views import OrganizationView, BuildingView

urlpatterns = [
    path('organizations/', OrganizationView.as_view(), name='organizations'),
    path('buildings/', BuildingView.as_view(), name='buildings'),
]