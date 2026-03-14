from django import forms as django_forms
from django.test import TestCase
from django.contrib.auth.models import User
from .forms import ApplicationForm
from .models import Company, Application


VALID_DATA = {
    'company_name': 'Acme Corp',
    'company_location': 'London',
    'company_website': 'https://acme.com',
    'job_title': 'Software Engineer',
    'salary_range': '50,000 - 60,000',
    'status': 'applied',
    'date_applied': '2026-03-01',
    'notes': 'Great role.',
}


class ApplicationFormValidationTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='pass')

    def _form(self, data):
        return ApplicationForm(data=data, user=self.user)

    def test_valid_form(self):
        form = self._form(VALID_DATA)
        self.assertTrue(form.is_valid(), form.errors)

    def test_missing_company_name(self):
        data = {**VALID_DATA, 'company_name': ''}
        form = self._form(data)
        self.assertFalse(form.is_valid())
        self.assertIn('company_name', form.errors)

    def test_missing_job_title(self):
        data = {**VALID_DATA, 'job_title': ''}
        form = self._form(data)
        self.assertFalse(form.is_valid())
        self.assertIn('job_title', form.errors)

    def test_missing_status(self):
        data = {**VALID_DATA, 'status': ''}
        form = self._form(data)
        self.assertFalse(form.is_valid())
        self.assertIn('status', form.errors)

    def test_missing_date_applied(self):
        data = {**VALID_DATA, 'date_applied': ''}
        form = self._form(data)
        self.assertFalse(form.is_valid())
        self.assertIn('date_applied', form.errors)

    def test_company_location_not_required(self):
        data = {**VALID_DATA, 'company_location': ''}
        form = self._form(data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_company_website_not_required(self):
        data = {**VALID_DATA, 'company_website': ''}
        form = self._form(data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_salary_range_not_required(self):
        data = {**VALID_DATA, 'salary_range': ''}
        form = self._form(data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_notes_not_required(self):
        data = {**VALID_DATA, 'notes': ''}
        form = self._form(data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_invalid_website_url(self):
        data = {**VALID_DATA, 'company_website': 'not-a-url'}
        form = self._form(data)
        self.assertFalse(form.is_valid())
        self.assertIn('company_website', form.errors)

    def test_invalid_status_choice(self):
        data = {**VALID_DATA, 'status': 'invalid_status'}
        form = self._form(data)
        self.assertFalse(form.is_valid())
        self.assertIn('status', form.errors)

    def test_invalid_date_format(self):
        data = {**VALID_DATA, 'date_applied': 'not-a-date'}
        form = self._form(data)
        self.assertFalse(form.is_valid())
        self.assertIn('date_applied', form.errors)


class ApplicationFormStructureTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='pass')

    def test_field_order(self):
        form = ApplicationForm(user=self.user)
        expected_order = [
            'company_name', 'company_location', 'company_website',
            'job_title', 'salary_range', 'status', 'date_applied', 'notes',
        ]
        self.assertEqual(list(form.fields.keys()), expected_order)

    def test_all_fields_have_form_control_class(self):
        form = ApplicationForm(user=self.user)
        for name, field in form.fields.items():
            self.assertIn(
                'form-control', field.widget.attrs.get('class', ''),
                msg=f"Field '{name}' is missing the form-control class"
            )

    def test_form_initialises_without_user(self):
        """Form should not crash when no user is passed."""
        form = ApplicationForm(data=VALID_DATA)
        self.assertIsNone(form.user)

    def test_date_applied_uses_date_input_widget(self):
        form = ApplicationForm(user=self.user)
        self.assertIsInstance(form.fields['date_applied'].widget, django_forms.DateInput)


class ApplicationFormSaveTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='pass')

    def _saved_form(self, data=None):
        """Mirrors the view pattern: form.save(commit=False), set user, then save."""
        form = ApplicationForm(data=data or VALID_DATA, user=self.user)
        self.assertTrue(form.is_valid(), form.errors)
        application = form.save(commit=False)
        application.user = self.user
        application.save()
        return application

    def test_save_creates_application(self):
        application = self._saved_form()
        self.assertIsInstance(application, Application)
        self.assertEqual(application.job_title, 'Software Engineer')
        self.assertEqual(application.status, 'applied')

    def test_save_creates_company(self):
        self._saved_form()
        self.assertTrue(Company.objects.filter(user=self.user, name='Acme Corp').exists())

    def test_save_company_uses_provided_location_and_website(self):
        self._saved_form()
        company = Company.objects.get(user=self.user, name='Acme Corp')
        self.assertEqual(company.location, 'London')
        self.assertEqual(company.website, 'https://acme.com')

    def test_save_links_application_to_company(self):
        application = self._saved_form()
        self.assertEqual(application.company.name, 'Acme Corp')

    def test_save_reuses_existing_company(self):
        """Saving twice with the same company name should not create a duplicate."""
        self._saved_form()
        self._saved_form()
        self.assertEqual(
            Company.objects.filter(user=self.user, name='Acme Corp').count(), 1
        )

    def test_save_without_commit_does_not_persist(self):
        form = ApplicationForm(data=VALID_DATA, user=self.user)
        self.assertTrue(form.is_valid())
        application = form.save(commit=False)
        self.assertIsNone(application.pk)
        self.assertEqual(Application.objects.count(), 0)

    def test_save_persists_to_database(self):
        self._saved_form()
        self.assertEqual(Application.objects.count(), 1)

    def test_save_application_has_correct_user_via_company(self):
        application = self._saved_form()
        self.assertEqual(application.company.user, self.user)
