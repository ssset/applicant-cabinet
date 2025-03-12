from django.test import TestCase
from rest_framework.test import APIClient
from users.models import CustomUser


class AuthTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_register_success(self):
        """
        Тест успешной регистрации
        """
        data = {
            'email': 'test@example.com',
            'password': 'password123',
            'password2': 'password123',
            'role': 'applicant'
        }
        response = self.client.post('/api/auth/register/', data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(CustomUser.objects.filter(email='test@example.com').exists())