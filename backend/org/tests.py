# org/tests.py
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from users.models import CustomUser
from .models import Organization, Building

class OrgTestCase(APITestCase):
    def setUp(self):
        self.register_url = reverse('register')
        self.login_url = reverse('login')
        self.buildings_url = reverse('buildings')
        self.org = Organization.objects.create(name='Test Org', email='org@example.com', phone='+1234567890',
                                               address='Test Address')

    def login_user(self, email, password):
        """Вспомогательный метод для логина и установки токена."""
        login_response = self.client.post(self.login_url, {'email': email, 'password': password}, format='json')
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        access_token = login_response.data['access']
        print(f"Access token for {email}: {access_token}")
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        return access_token

    def test_create_building(self):
        admin_data = {
            'email': 'admin5@example.com',
            'password': 'adminpass123',
            'password2': 'adminpass123',
            'consent_to_data_processing': True
        }
        self.client.post(self.register_url, admin_data, format='json')
        admin = CustomUser.objects.get(email='admin5@example.com')
        admin.is_verified = True
        admin.role = 'admin_org'
        admin.organization = self.org
        admin.save()

        self.client.credentials()
        self.login_user('admin5@example.com', 'adminpass123')

        building_data = {
            'name': 'Building 1',
            'address': 'Test Address 1',
            'phone': '+1234567890',
            'email': 'building1@example.com'
        }
        response = self.client.post(self.buildings_url, building_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Building 1')
        self.assertEqual(Building.objects.count(), 1)

    def test_get_buildings(self):
        admin_data = {
            'email': 'admin6@example.com',
            'password': 'adminpass123',
            'password2': 'adminpass123',
            'consent_to_data_processing': True
        }
        self.client.post(self.register_url, admin_data, format='json')
        admin = CustomUser.objects.get(email='admin6@example.com')
        admin.is_verified = True
        admin.role = 'admin_org'
        admin.organization = self.org
        admin.save()

        Building.objects.create(
            organization=self.org,
            name='Building 1',
            address='Test Address 1',
            phone='+1234567890',
            email='building1@example.com'
        )

        self.client.credentials()
        self.login_user('admin6@example.com', 'adminpass123')

        response = self.client.get(self.buildings_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Building 1')

    def test_patch_building(self):
        admin_data = {
            'email': 'admin7@example.com',
            'password': 'adminpass123',
            'password2': 'adminpass123',
            'consent_to_data_processing': True
        }
        self.client.post(self.register_url, admin_data, format='json')
        admin = CustomUser.objects.get(email='admin7@example.com')
        admin.is_verified = True
        admin.role = 'admin_org'
        admin.organization = self.org
        admin.save()

        building = Building.objects.create(
            organization=self.org,
            name='Building 1',
            address='Test Address 1',
            phone='+1234567890',
            email='building1@example.com'
        )

        self.client.credentials()
        self.login_user('admin7@example.com', 'adminpass123')

        updated_data = {
            'id': building.id,
            'address': 'Updated Address'
        }
        response = self.client.patch(self.buildings_url, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['address'], 'Updated Address')

    def test_delete_building(self):
        admin_data = {
            'email': 'admin8@example.com',
            'password': 'adminpass123',
            'password2': 'adminpass123',
            'consent_to_data_processing': True
        }
        self.client.post(self.register_url, admin_data, format='json')
        admin = CustomUser.objects.get(email='admin8@example.com')
        admin.is_verified = True
        admin.role = 'admin_org'
        admin.organization = self.org
        admin.save()

        building = Building.objects.create(
            organization=self.org,
            name='Building 1',
            address='Test Address 1',
            phone='+1234567890',
            email='building1@example.com'
        )

        self.client.credentials()
        self.login_user('admin8@example.com', 'adminpass123')

        response = self.client.delete(f"{self.buildings_url}?id={building.id}", format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Building.objects.count(), 0)

    def test_duplicate_building(self):
        admin_data = {
            'email': 'admin9@example.com',
            'password': 'adminpass123',
            'password2': 'adminpass123',
            'consent_to_data_processing': True
        }
        self.client.post(self.register_url, admin_data, format='json')
        admin = CustomUser.objects.get(email='admin9@example.com')
        admin.is_verified = True
        admin.role = 'admin_org'
        admin.organization = self.org
        admin.save()

        Building.objects.create(
            organization=self.org,
            name='Building 1',
            address='Test Address 1',
            phone='+1234567890',
            email='building1@example.com'
        )

        self.client.credentials()
        self.login_user('admin9@example.com', 'adminpass123')

        duplicate_data = {
            'name': 'Building 1',
            'address': 'Test Address 2',
            'phone': '+1234567891',
            'email': 'building2@example.com'
        }
        response = self.client.post(self.buildings_url, duplicate_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)