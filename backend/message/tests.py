# message/tests.py
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from users.models import CustomUser
from org.models import Organization, BuildingSpecialty, Building, Specialty
from applications.models import Application
from .models import Chat, Message

class ChatTestCase(APITestCase):
    def setUp(self):
        self.register_url = reverse('register')
        self.login_url = reverse('login')
        self.chat_list_url = reverse('chat_list')
        self.chat_detail_url = reverse('chat_detail')

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

    def test_applicant_create_chat(self):
        """
        Тест создания чата абитуриентом.
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

        # Создаём заявку, чтобы абитуриент мог создать чат
        Application.objects.create(
            applicant=applicant,
            building_specialty=self.building_specialty,
            priority=1
        )

        self.client.credentials()
        self.login_user('applicant@example.com', 'apppass123')

        response = self.client.post(self.chat_list_url, {
            'organization_id': self.org.id
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Chat.objects.count(), 1)

    def test_moderator_get_chats(self):
        """
        Тест получения списка чатов модератором.
        """
        moderator_data = {
            'email': 'moderator@example.com',
            'password': 'modpass123',
            'password2': 'modpass123',
            'consent_to_data_processing': True
        }
        self.client.post(self.register_url, moderator_data, format='json')
        moderator = CustomUser.objects.get(email='moderator@example.com')
        moderator.is_verified = True
        moderator.role = 'moderator'
        moderator.organization = self.org
        moderator.save()

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

        chat = Chat.objects.create(
            applicant=applicant,
            organization=self.org
        )

        self.client.credentials()
        self.login_user('moderator@example.com', 'modpass123')

        response = self.client.get(self.chat_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_send_message(self):
        """
        Тест отправки сообщения в чат.
        """
        moderator_data = {
            'email': 'moderator2@example.com',
            'password': 'modpass123',
            'password2': 'modpass123',
            'consent_to_data_processing': True
        }
        self.client.post(self.register_url, moderator_data, format='json')
        moderator = CustomUser.objects.get(email='moderator2@example.com')
        moderator.is_verified = True
        moderator.role = 'moderator'
        moderator.organization = self.org
        moderator.save()

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

        Application.objects.create(
            applicant=applicant,
            building_specialty=self.building_specialty,
            priority=1
        )

        chat = Chat.objects.create(
            applicant=applicant,
            organization=self.org
        )

        self.client.credentials()
        self.login_user('moderator2@example.com', 'modpass123')

        response = self.client.post(self.chat_detail_url, {
            'chat_id': chat.id,
            'content': 'Hello, applicant!'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Message.objects.count(), 1)