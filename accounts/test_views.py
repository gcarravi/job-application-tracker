from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User


class RegisterViewTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.url = reverse('register')
        self.valid_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'Str0ng!Pass99',
            'password2': 'Str0ng!Pass99',
        }

    def test_valid_registration_creates_user(self):
        self.client.post(self.url, self.valid_data)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_valid_registration_logs_user_in(self):
        self.client.post(self.url, self.valid_data)
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

    def test_valid_registration_redirects_to_home(self):
        response = self.client.post(self.url, self.valid_data)
        self.assertRedirects(response, reverse('home'))

    def test_mismatched_passwords_rerenders_form(self):
        data = {**self.valid_data, 'password2': 'different'}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/register.html')
        self.assertFalse(User.objects.filter(username='newuser').exists())

    def test_missing_email_rerenders_form(self):
        data = {**self.valid_data, 'email': ''}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='newuser').exists())

    def test_duplicate_username_rerenders_form(self):
        User.objects.create_user(username='newuser', password='pass')
        response = self.client.post(self.url, self.valid_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.filter(username='newuser').count(), 1)

    def test_get_renders_blank_form(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/register.html')
