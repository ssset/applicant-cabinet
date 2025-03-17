from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from users.models import CustomUser


class AuthTestCase(TestCase):
    def setUp(self):
        self.register_url = reverse('register')
        self.verify_url = reverse('verify')
        self.login_url = reverse('login')
        self.user_data = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'password2': 'testpass123',
            'consent_to_data_processing': True
        }

    def test_register(self):
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_verify(self):
        self.client.post(self.register_url, self.user_data, format='json')
        user = CustomUser.objects.get(email='test@example.com')
        verify_data = {'email': 'test@example.com', 'verification_code': user.verification_code}
        response = self.client.post(self.verify_url, verify_data, format=json)
        self.assertEqual(response.status_code, status=status.HTTP_200_OK)

    def test_login(self):
        self.client.post(self.register_url, self.user_data, format='json')
        user = CustomUser.objects.get(email='test@example.com')
        user.is_verified = True
        user.save()
        response = self.client.post(self.login_url, {'email': 'test@example.com', 'password': 'testpass123'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)