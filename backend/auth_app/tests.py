from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from users.models import CustomUser, Organization, Building
from django.contrib.auth import authenticate


class AuthTestCase(APITestCase):
    def setUp(self):
        self.register_url = reverse('register')
        self.verify_url = reverse('verify_email')
        self.moderators_url = reverse('moderators')
        self.login_url = reverse('login')
        self.buildings_url = reverse('buildings')
        self.user_data = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'password2': 'testpass123',
            'consent_to_data_processing': True
        }
        self.org = Organization.objects.create(name='Test Org', email='org@example.com', phone='+1234567890',
                                               address='Test Address')

    def login_user(self, email, password):
        """Вспомогательный метод для логина и установки токена."""
        login_response = self.client.post(self.login_url, {'email': email, 'password': password}, format='json')
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        access_token = login_response.data['access']
        print(f"Access token for {email}: {access_token}")  # Убедимся, что токен выводится
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        return access_token

    def test_register(self):
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_verify(self):
        self.client.post(self.register_url, self.user_data, format='json')
        user = CustomUser.objects.get(email='test@example.com')
        verify_data = {'email': 'test@example.com', 'verification_code': user.verification_code}
        response = self.client.post(self.verify_url, verify_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_login(self):
        self.client.post(self.register_url, self.user_data, format='json')
        user = CustomUser.objects.get(email='test@example.com')
        user.is_verified = True
        user.save()
        response = self.client.post(self.login_url, {'email': 'test@example.com', 'password': 'testpass123'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def create_moderator(self):
        admin_data = {
            'email': 'admin@example.com',
            'password': 'adminpass123',
            'password2': 'adminpass123',
            'consent_to_data_processing': True
        }
        self.client.post(self.register_url, admin_data, format='json')
        admin = CustomUser.objects.get(email='admin@example.com')
        admin.is_verified = True
        admin.role = 'admin_org'
        admin.organization = self.org
        admin.save()

        # Логинимся перед запросом
        self.client.credentials()  # Сбрасываем заголовки
        self.login_user('admin@example.com', 'adminpass123')

        moderator_data = {
            'email': 'mod@example.com',
            'password': 'modpass123',
            'password2': 'modpass123',
            'consent_to_data_processing': True
        }
        response = self.client.post(self.moderators_url, moderator_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CustomUser.objects.filter(email='mod@example.com', role='moderator').count(), 1)

    def test_get_moderators(self):
        admin_data = {
            'email': 'admin2@example.com',
            'password': 'adminpass123',
            'password2': 'adminpass123',
            'consent_to_data_processing': True
        }
        self.client.post(self.register_url, admin_data, format='json')
        admin = CustomUser.objects.get(email='admin2@example.com')
        admin.is_verified = True
        admin.role = 'admin_org'
        admin.organization = self.org
        admin.save()

        moderator = CustomUser.objects.create_user(email='mod1@example.com', password='modpass123', role='moderator',
                                                organization=self.org, is_verified=True, consent_to_data_processing=True)

        # Логинимся перед запросом
        self.client.credentials()  # Сбрасываем заголовки
        self.login_user('admin2@example.com', 'adminpass123')

        response = self.client.get(self.moderators_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)
        self.assertEqual(response.data[0]['email'], 'mod1@example.com')

    def test_patch_moderator(self):
        admin_data = {
            'email': 'admin3@example.com',
            'password': 'adminpass123',
            'password2': 'adminpass123',
            'consent_to_data_processing': True
        }
        self.client.post(self.register_url, admin_data, format='json')
        admin = CustomUser.objects.get(email='admin3@example.com')
        admin.is_verified = True
        admin.role = 'admin_org'
        admin.organization = self.org
        admin.save()

        moderator = CustomUser.objects.create_user(email='mod2@example.com', password='modpass123', role='moderator',
                                                   organization=self.org, is_verified=True,
                                                   consent_to_data_processing=True)

        # Логинимся перед запросом
        self.client.credentials()  # Сбрасываем заголовки
        self.login_user('admin3@example.com', 'adminpass123')

        # Добавляем password и password2 в updated_data
        updated_data = {
            'id': moderator.id,
            'email': 'mod2_updated@example.com',
            'password': 'modpass123',  # Используем тот же пароль
            'password2': 'modpass123',  # Повторяем пароль
        }
        response = self.client.patch(self.moderators_url, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'mod2_updated@example.com')

    def test_delete_moderator(self):
        admin_data = {
            'email': 'admin4@example.com',
            'password': 'adminpass123',
            'password2': 'adminpass123',
            'consent_to_data_processing': True
        }
        self.client.post(self.register_url, admin_data, format='json')
        admin = CustomUser.objects.get(email='admin4@example.com')
        admin.is_verified = True
        admin.role = 'admin_org'
        admin.organization = self.org
        admin.save()

        moderator = CustomUser.objects.create_user(email='mod3@example.com', password='modpass123', role='moderator',
                                                   organization=self.org, is_verified=True,
                                                   consent_to_data_processing=True)

        # Логинимся перед запросом
        self.client.credentials()  # Сбрасываем заголовки
        self.login_user('admin4@example.com', 'adminpass123')

        # Передаём id как query-параметр
        response = self.client.delete(f"{self.moderators_url}?id={moderator.id}", format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(CustomUser.objects.filter(email='mod3@example.com').count(), 0)


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

        # Логинимся перед запросом
        self.client.credentials()  # Сбрасываем заголовки
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

        # Создаём корпус
        Building.objects.create(
            organization=self.org,
            name='Building 1',
            address='Test Address 1',
            phone='+1234567890',
            email='building1@example.com'
        )

        # Логинимся перед запросом
        self.client.credentials()  # Сбрасываем заголовки
        self.login_user('admin6@example.com', 'adminpass123')

        response = self.client.get(self.buildings_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Building 1')

    # auth_app/tests.py
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

        # Добавляем отладку
        admin_refreshed = CustomUser.objects.get(email='admin7@example.com')

        # Создаём корпус
        building = Building.objects.create(
            organization=self.org,
            name='Building 1',
            address='Test Address 1',
            phone='+1234567890',
            email='building1@example.com'
        )

        # Логинимся перед запросом
        self.client.credentials()  # Сбрасываем заголовки
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

        # Создаём корпус
        building = Building.objects.create(
            organization=self.org,
            name='Building 1',
            address='Test Address 1',
            phone='+1234567890',
            email='building1@example.com'
        )

        # Логинимся перед запросом
        self.client.credentials()  # Сбрасываем заголовки
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

        # Создаём первый корпус
        Building.objects.create(
            organization=self.org,
            name='Building 1',
            address='Test Address 1',
            phone='+1234567890',
            email='building1@example.com'
        )

        # Логинимся перед запросом
        self.client.credentials()  # Сбрасываем заголовки
        self.login_user('admin9@example.com', 'adminpass123')

        # Пытаемся создать корпус с тем же именем
        duplicate_data = {
            'name': 'Building 1',
            'address': 'Test Address 2',
            'phone': '+1234567891',
            'email': 'building2@example.com'
        }
        response = self.client.post(self.buildings_url, duplicate_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
