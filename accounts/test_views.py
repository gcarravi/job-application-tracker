from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch


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


class UploadPhotoViewTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.url = reverse('upload_photo')
        self.user = User.objects.create_user(username='testuser', password='pass')
        self.client.login(username='testuser', password='pass')

    def _fake_photo(self):
        # Minimal valid JPEG header bytes
        return SimpleUploadedFile('photo.jpg', b'\xff\xd8\xff\xe0' + b'\x00' * 100, content_type='image/jpeg')

    def test_requires_login(self):
        self.client.logout()
        response = self.client.post(self.url)
        self.assertRedirects(response, f'/accounts/login/?next={self.url}')

    def test_no_file_returns_400(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content, {'success': False, 'error': 'No file provided'})

    @patch('cloudinary.uploader.upload')
    def test_valid_upload_returns_success(self, mock_upload):
        mock_upload.return_value = {'public_id': 'test/photo123', 'version': 1, 'resource_type': 'image', 'type': 'upload'}
        response = self.client.post(self.url, {'photo': self._fake_photo()})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('url', data)

    @patch('cloudinary.uploader.upload')
    def test_valid_upload_saves_photo_to_profile(self, mock_upload):
        mock_upload.return_value = {'public_id': 'test/photo123', 'version': 1, 'resource_type': 'image', 'type': 'upload'}
        self.client.post(self.url, {'photo': self._fake_photo()})
        self.user.profile.refresh_from_db()
        self.assertTrue(bool(self.user.profile.photo))
