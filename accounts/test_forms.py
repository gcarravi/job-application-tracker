from django.test import TestCase
from django.contrib.auth.models import User
from .forms import RegisterForm


VALID_DATA = {
    'username': 'newuser',
    'email': 'newuser@example.com',
    'password1': 'TestPass123!',
    'password2': 'TestPass123!',
}


class RegisterFormValidationTests(TestCase):

    def test_valid_form(self):
        form = RegisterForm(data=VALID_DATA)
        self.assertTrue(form.is_valid(), form.errors)

    def test_missing_username(self):
        data = {**VALID_DATA, 'username': ''}
        form = RegisterForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)

    def test_missing_email(self):
        data = {**VALID_DATA, 'email': ''}
        form = RegisterForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_invalid_email_format(self):
        data = {**VALID_DATA, 'email': 'not-an-email'}
        form = RegisterForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_password_mismatch(self):
        data = {**VALID_DATA, 'password2': 'DifferentPass456!'}
        form = RegisterForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)

    def test_missing_password1(self):
        data = {**VALID_DATA, 'password1': ''}
        form = RegisterForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('password1', form.errors)

    def test_missing_password2(self):
        data = {**VALID_DATA, 'password2': ''}
        form = RegisterForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)

    def test_duplicate_username(self):
        User.objects.create_user(username='newuser', password='pass')
        form = RegisterForm(data=VALID_DATA)
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)

    def test_password_too_short(self):
        data = {**VALID_DATA, 'password1': 'short', 'password2': 'short'}
        form = RegisterForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)

    def test_entirely_numeric_password(self):
        data = {**VALID_DATA, 'password1': '12345678', 'password2': '12345678'}
        form = RegisterForm(data=data)
        self.assertFalse(form.is_valid())


class RegisterFormStructureTests(TestCase):

    def test_email_field_is_present(self):
        form = RegisterForm()
        self.assertIn('email', form.fields)

    def test_email_field_is_required(self):
        form = RegisterForm()
        self.assertTrue(form.fields['email'].required)

    def test_expected_fields_present(self):
        form = RegisterForm()
        for field in ['username', 'email', 'password1', 'password2']:
            self.assertIn(field, form.fields)
