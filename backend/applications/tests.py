# applications/tests.py
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from users.models import CustomUser
from org.models import Organization, Building, Specialty, BuildingSpecialty
from .models import Application


class ApplicationTestCase(APITestCase):
    def setUp(self):
        self.register_url = reverse('register')
        self.login_url = reverse('login')
        self.applications_url = reverse('applications')
        self.available_specialties_url = reverse('available_specialties')

        self.org = Organization.objects.create(
            name='Test Org',
            email='org@example.com',
            phone='+1234567890',
            address='Test Address'
        )
        self.building = Building.objects.create(
            organization=self.org,
            name='Building 1',
            address='Test Address 1',
            phone='+1234567890',
            email='building1@example.com'
        )
        self.specialty = Specialty.objects.create(
            organization=self.org,
            code='09.02.07',
            name='Информационные системы и программирование'
        )
        self.building_specialty = BuildingSpecialty.objects.create(
            building=self.building,
            specialty=self.specialty,
            budget_places=30,
            commercial_places=20,
            commercial_price='150000.00'
        )

    def login_user(self, email, password):
        """Вспомогательный метод для логина и установки токена."""
        login_response = self.client.post(self.login_url, {'email': email, 'password': password}, format='json')
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        access_token = login_response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        return access_token

    def test_submit_application(self):
        """
        Тест подачи заявки абитуриентом.
        """
        applicant_data = {
            'email': 'applicant@example.com',
            'password': 'apppass123',
            'password2': 'apppass123',
            'consent_to_data_processing': True
        }
        self.client.post(self.register_url, applicant_data, format='json')
        applicant = CustomUser.objects.get(email='applicant@example.com')
        applicant.is_verified = True
        applicant.role = 'applicant'
        applicant.save()

        self.client.credentials()
        self.login_user('applicant@example.com', 'apppass123')

        application_data = {
            'building_specialty_id': self.building_specialty.id,
            'priority': 1,
            'course': 1,
            'study_form': 'full_time',
            'funding_basis': 'budget',
            'dormitory_needed': True,
            'first_time_education': True,
            'info_source': 'Website'
        }
        response = self.client.post(self.applications_url, application_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['study_form'], 'full_time')
        self.assertEqual(Application.objects.count(), 1)

    def test_get_applications(self):
        """
        Тест получения списка заявок.
        """
        applicant_data = {
            'email': 'applicant2@example.com',
            'password': 'apppass123',
            'password2': 'apppass123',
            'consent_to_data_processing': True
        }
        self.client.post(self.register_url, applicant_data, format='json')
        applicant = CustomUser.objects.get(email='applicant2@example.com')
        applicant.is_verified = True
        applicant.role = 'applicant'
        applicant.save()

        Application.objects.create(
            applicant=applicant,
            building_specialty=self.building_specialty,
            priority=1
        )

        self.client.credentials()
        self.login_user('applicant2@example.com', 'apppass123')

        response = self.client.get(self.applications_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_available_specialties(self):
        """
        Тест получения списка доступных специальностей.
        """
        applicant_data = {
            'email': 'applicant3@example.com',
            'password': 'apppass123',
            'password2': 'apppass123',
            'consent_to_data_processing': True
        }
        self.client.post(self.register_url, applicant_data, format='json')
        applicant = CustomUser.objects.get(email='applicant3@example.com')
        applicant.is_verified = True
        applicant.role = 'applicant'
        applicant.save()

        self.client.credentials()
        self.login_user('applicant3@example.com', 'apppass123')

        response = self.client.get(self.available_specialties_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['code'], '09.02.07')
