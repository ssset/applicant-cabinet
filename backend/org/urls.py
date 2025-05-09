
from django.urls import path
from .views import *

urlpatterns = [
    path('organizations/', OrganizationView.as_view(), name='organizations'),
    path('buildings/', BuildingView.as_view(), name='buildings'),
    path('specialties/', SpecialtyView.as_view(), name='specialties'),
    path('building-specialties/', BuildingSpecialtyView.as_view(), name='building_specialties'),
    path('apply/', OrganizationApplicationView.as_view(), name='organization-apply'),
    path('payment/', PaymentView.as_view(), name='payment'),
    path('payment/webhook/', PaymentWebhookView.as_view(), name='payment-webhook'),
]
