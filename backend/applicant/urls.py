from django.urls import path, include
from auth_app.views import ApplicantProfileView

urlpatterns = [
    path('api/auth/', include('auth_app.urls')),
    path('api/profile/', ApplicantProfileView.as_view(), name='applicant_profile'),
]