import json
from datetime import date, timedelta
from unittest.mock import patch, MagicMock

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile

from .models import Application, Company, Contact, Interview, Document


class PostViewTestBase(TestCase):
    """Shared fixtures for all POST view tests."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='pass')
        self.other_user = User.objects.create_user(username='other', password='pass')
        self.client.login(username='testuser', password='pass')

        self.company = Company.objects.create(user=self.user, name='Acme Corp')
        self.application = Application.objects.create(
            user=self.user,
            company=self.company,
            job_title='Developer',
            status='applied',
            date_applied=date.today(),
        )
        self.contact = Contact.objects.create(
            user=self.user,
            first_name='Alice',
            last_name='Smith',
            job_title='Recruiter',
        )
        self.interview = Interview.objects.create(
            application=self.application,
            interview_type='Human Resources',
            date=timezone.make_aware(timezone.datetime(2026, 4, 1, 10, 0)),
        )

    # ── helpers ──────────────────────────────────────────────────────────────

    def _json_post(self, url, data):
        return self.client.post(url, json.dumps(data), content_type='application/json')

    def _valid_application_post_data(self):
        return {
            'company_name': 'New Co',
            'company_location': 'London',
            'company_website': '',
            'job_title': 'Engineer',
            'salary_range': '',
            'status': 'applied',
            'date_applied': str(date.today()),
            'notes': '',
        }


# ── HomeView POST ─────────────────────────────────────────────────────────────

class HomeViewPostTests(PostViewTestBase):

    def test_valid_form_creates_application_and_redirects_to_tracker(self):
        url = reverse('home')
        response = self.client.post(url, self._valid_application_post_data())
        self.assertRedirects(response, reverse('tracker'))
        self.assertTrue(Application.objects.filter(job_title='Engineer', user=self.user).exists())

    def test_invalid_form_rerenders_home(self):
        url = reverse('home')
        response = self.client.post(url, {'job_title': ''})  # missing required fields
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')

    def test_requires_login(self):
        self.client.logout()
        response = self.client.post(reverse('home'), self._valid_application_post_data())
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('home')}")


# ── TrackerBoardView POST ─────────────────────────────────────────────────────

class TrackerBoardViewPostTests(PostViewTestBase):

    def test_valid_form_creates_application_and_redirects(self):
        url = reverse('tracker')
        response = self.client.post(url, self._valid_application_post_data())
        self.assertRedirects(response, reverse('tracker'))
        self.assertTrue(Application.objects.filter(job_title='Engineer', user=self.user).exists())

    def test_invalid_form_rerenders_tracker(self):
        url = reverse('tracker')
        response = self.client.post(url, {'job_title': ''})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tracker/tracker.html')

    def test_requires_login(self):
        self.client.logout()
        response = self.client.post(reverse('tracker'), self._valid_application_post_data())
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('tracker')}")


# ── delete_job ────────────────────────────────────────────────────────────────

class DeleteJobTests(PostViewTestBase):

    def test_deletes_job_and_returns_success(self):
        url = reverse('delete_job', args=[self.application.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'success': True})
        self.assertFalse(Application.objects.filter(id=self.application.id).exists())

    def test_get_returns_400(self):
        url = reverse('delete_job', args=[self.application.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

    def test_nonexistent_job_returns_404(self):
        url = reverse('delete_job', args=[9999])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)


# ── update_job_status ─────────────────────────────────────────────────────────

class UpdateJobStatusTests(PostViewTestBase):

    def test_updates_status_and_returns_success(self):
        url = reverse('update-job-status', args=[self.application.id])
        response = self._json_post(url, {'status': 'interviewing'})
        self.assertEqual(response.status_code, 200)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, 'interviewing')

    def test_invalid_status_returns_400(self):
        url = reverse('update-job-status', args=[self.application.id])
        response = self._json_post(url, {'status': 'not_a_status'})
        self.assertEqual(response.status_code, 400)

    def test_nonexistent_job_returns_404(self):
        url = reverse('update-job-status', args=[9999])
        response = self._json_post(url, {'status': 'applied'})
        self.assertEqual(response.status_code, 404)

    def test_invalid_json_returns_400(self):
        url = reverse('update-job-status', args=[self.application.id])
        response = self.client.post(url, 'not json', content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_get_returns_400(self):
        url = reverse('update-job-status', args=[self.application.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)


# ── update_job ────────────────────────────────────────────────────────────────

class UpdateJobTests(PostViewTestBase):

    def test_updates_job_fields(self):
        url = reverse('update_job', args=[self.application.id])
        response = self._json_post(url, {'job_title': 'Senior Developer', 'salary_range': '£80k'})
        self.assertEqual(response.status_code, 200)
        self.application.refresh_from_db()
        self.assertEqual(self.application.job_title, 'Senior Developer')
        self.assertEqual(self.application.salary_range, '£80k')

    def test_sets_recruiter(self):
        url = reverse('update_job', args=[self.application.id])
        response = self._json_post(url, {'recruiter_id': self.contact.id})
        self.assertEqual(response.status_code, 200)
        self.application.refresh_from_db()
        self.assertEqual(self.application.recruiter, self.contact)

    def test_clears_recruiter_when_empty(self):
        self.application.recruiter = self.contact
        self.application.save()
        url = reverse('update_job', args=[self.application.id])
        response = self._json_post(url, {'recruiter_id': ''})
        self.assertEqual(response.status_code, 200)
        self.application.refresh_from_db()
        self.assertIsNone(self.application.recruiter)

    def test_get_returns_400(self):
        url = reverse('update_job', args=[self.application.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

    def test_nonexistent_job_returns_404(self):
        url = reverse('update_job', args=[9999])
        response = self._json_post(url, {'job_title': 'X'})
        self.assertEqual(response.status_code, 404)


# ── save_interview ────────────────────────────────────────────────────────────

class SaveInterviewTests(PostViewTestBase):

    def test_creates_interview_and_returns_id(self):
        url = reverse('save_interview', args=[self.application.id])
        response = self._json_post(url, {
            'interview_type': 'Technical Interview',
            'date': '2026-05-10T09:30',
            'notes': 'Be on time',
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('id', data)

    def test_missing_date_returns_400(self):
        url = reverse('save_interview', args=[self.application.id])
        response = self._json_post(url, {'interview_type': 'Technical Interview'})
        self.assertEqual(response.status_code, 400)

    def test_invalid_date_returns_400(self):
        url = reverse('save_interview', args=[self.application.id])
        response = self._json_post(url, {'date': 'not-a-date'})
        self.assertEqual(response.status_code, 400)

    def test_sets_interviewers(self):
        url = reverse('save_interview', args=[self.application.id])
        response = self._json_post(url, {
            'date': '2026-05-10T09:30',
            'interviewer_ids': [self.contact.id],
        })
        self.assertEqual(response.status_code, 200)
        iv_id = response.json()['id']
        iv = Interview.objects.get(id=iv_id)
        self.assertIn(self.contact, iv.interviewers.all())

    def test_get_returns_400(self):
        url = reverse('save_interview', args=[self.application.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

    def test_requires_login(self):
        self.client.logout()
        url = reverse('save_interview', args=[self.application.id])
        response = self._json_post(url, {'date': '2026-05-10T09:30'})
        self.assertEqual(response.status_code, 302)

    def test_other_users_application_returns_404(self):
        other_company = Company.objects.create(user=self.other_user, name='Other Co')
        other_app = Application.objects.create(
            user=self.other_user, company=other_company,
            job_title='Other Job', status='applied', date_applied=date.today(),
        )
        url = reverse('save_interview', args=[other_app.id])
        response = self._json_post(url, {'date': '2026-05-10T09:30'})
        self.assertEqual(response.status_code, 404)


# ── update_interview ──────────────────────────────────────────────────────────

class UpdateInterviewTests(PostViewTestBase):

    def test_updates_interview_fields(self):
        url = reverse('update_interview', args=[self.interview.id])
        response = self._json_post(url, {
            'interview_type': 'Final',
            'date': '2026-05-15T14:00',
            'result': 'Passed',
            'notes': 'Went well',
        })
        self.assertEqual(response.status_code, 200)
        self.interview.refresh_from_db()
        self.assertEqual(self.interview.interview_type, 'Final')
        self.assertEqual(self.interview.result, 'Passed')

    def test_updates_interviewers(self):
        url = reverse('update_interview', args=[self.interview.id])
        response = self._json_post(url, {'interviewer_ids': [self.contact.id]})
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.contact, self.interview.interviewers.all())

    def test_get_returns_400(self):
        url = reverse('update_interview', args=[self.interview.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

    def test_requires_login(self):
        self.client.logout()
        url = reverse('update_interview', args=[self.interview.id])
        response = self._json_post(url, {'result': 'Passed'})
        self.assertEqual(response.status_code, 302)

    def test_other_users_interview_returns_404(self):
        other_company = Company.objects.create(user=self.other_user, name='Other Co')
        other_app = Application.objects.create(
            user=self.other_user, company=other_company,
            job_title='Other Job', status='applied', date_applied=date.today(),
        )
        other_iv = Interview.objects.create(
            application=other_app, interview_type='Human Resources',
            date=timezone.make_aware(timezone.datetime(2026, 4, 1, 10, 0)),
        )
        url = reverse('update_interview', args=[other_iv.id])
        response = self._json_post(url, {'result': 'Passed'})
        self.assertEqual(response.status_code, 404)


# ── delete_interview ──────────────────────────────────────────────────────────

class DeleteInterviewTests(PostViewTestBase):

    def test_deletes_interview_and_returns_success(self):
        url = reverse('delete_interview', args=[self.interview.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'success': True})
        self.assertFalse(Interview.objects.filter(id=self.interview.id).exists())

    def test_get_returns_400(self):
        url = reverse('delete_interview', args=[self.interview.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

    def test_requires_login(self):
        self.client.logout()
        url = reverse('delete_interview', args=[self.interview.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

    def test_other_users_interview_returns_404(self):
        other_company = Company.objects.create(user=self.other_user, name='Other Co')
        other_app = Application.objects.create(
            user=self.other_user, company=other_company,
            job_title='Other Job', status='applied', date_applied=date.today(),
        )
        other_iv = Interview.objects.create(
            application=other_app, interview_type='Human Resources',
            date=timezone.make_aware(timezone.datetime(2026, 4, 1, 10, 0)),
        )
        url = reverse('delete_interview', args=[other_iv.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)


# ── save_contact ──────────────────────────────────────────────────────────────

class SaveContactTests(PostViewTestBase):

    def test_creates_contact_and_returns_data(self):
        url = reverse('save_contact')
        response = self._json_post(url, {
            'first_name': 'Bob',
            'last_name': 'Jones',
            'job_title': 'Engineer',
            'email': 'bob@example.com',
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertTrue(Contact.objects.filter(first_name='Bob', user=self.user).exists())

    def test_missing_first_name_returns_400(self):
        url = reverse('save_contact')
        response = self._json_post(url, {'last_name': 'Jones'})
        self.assertEqual(response.status_code, 400)

    def test_get_returns_400(self):
        url = reverse('save_contact')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

    def test_requires_login(self):
        self.client.logout()
        url = reverse('save_contact')
        response = self._json_post(url, {'first_name': 'Bob'})
        self.assertEqual(response.status_code, 302)


# ── update_contact ────────────────────────────────────────────────────────────

class UpdateContactTests(PostViewTestBase):

    def test_updates_contact_fields(self):
        url = reverse('update_contact', args=[self.contact.id])
        response = self._json_post(url, {
            'first_name': 'Alicia',
            'last_name': 'Brown',
            'email': 'alicia@example.com',
            'job_title': 'HR Manager',
        })
        self.assertEqual(response.status_code, 200)
        self.contact.refresh_from_db()
        self.assertEqual(self.contact.first_name, 'Alicia')
        self.assertEqual(self.contact.email, 'alicia@example.com')

    def test_get_returns_400(self):
        url = reverse('update_contact', args=[self.contact.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

    def test_requires_login(self):
        self.client.logout()
        url = reverse('update_contact', args=[self.contact.id])
        response = self._json_post(url, {'first_name': 'X'})
        self.assertEqual(response.status_code, 302)

    def test_other_users_contact_returns_404(self):
        other_contact = Contact.objects.create(user=self.other_user, first_name='Eve')
        url = reverse('update_contact', args=[other_contact.id])
        response = self._json_post(url, {'first_name': 'Changed'})
        self.assertEqual(response.status_code, 404)


# ── delete_contact ────────────────────────────────────────────────────────────

class DeleteContactTests(PostViewTestBase):

    def test_deletes_contact_and_returns_success(self):
        url = reverse('delete_contact', args=[self.contact.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'success': True})
        self.assertFalse(Contact.objects.filter(id=self.contact.id).exists())

    def test_get_returns_400(self):
        url = reverse('delete_contact', args=[self.contact.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

    def test_requires_login(self):
        self.client.logout()
        url = reverse('delete_contact', args=[self.contact.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

    def test_other_users_contact_returns_404(self):
        other_contact = Contact.objects.create(user=self.other_user, first_name='Eve')
        url = reverse('delete_contact', args=[other_contact.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)


# ── CompanyCreateView ─────────────────────────────────────────────────────────

class CompanyCreateViewTests(PostViewTestBase):

    def test_creates_company_and_redirects(self):
        url = reverse('company_add')
        response = self.client.post(url, {'name': 'New Co', 'location': 'Paris', 'website': ''})
        self.assertRedirects(response, reverse('company_list'))
        self.assertTrue(Company.objects.filter(name='New Co', user=self.user).exists())

    def test_missing_name_rerenders_form(self):
        url = reverse('company_add')
        response = self.client.post(url, {'name': '', 'location': 'Paris'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tracker/company_form.html')

    def test_requires_login(self):
        self.client.logout()
        url = reverse('company_add')
        response = self.client.post(url, {'name': 'New Co'})
        self.assertEqual(response.status_code, 302)


# ── CompanyUpdateView ─────────────────────────────────────────────────────────

class CompanyUpdateViewTests(PostViewTestBase):

    def test_updates_company_and_redirects(self):
        url = reverse('company_edit', args=[self.company.pk])
        response = self.client.post(url, {'name': 'Updated Corp', 'location': '', 'website': ''})
        self.assertRedirects(response, reverse('company_list'))
        self.company.refresh_from_db()
        self.assertEqual(self.company.name, 'Updated Corp')

    def test_other_users_company_returns_404(self):
        other_company = Company.objects.create(user=self.other_user, name='Other Co')
        url = reverse('company_edit', args=[other_company.pk])
        response = self.client.post(url, {'name': 'Hacked', 'location': '', 'website': ''})
        self.assertEqual(response.status_code, 404)

    def test_requires_login(self):
        self.client.logout()
        url = reverse('company_edit', args=[self.company.pk])
        response = self.client.post(url, {'name': 'X'})
        self.assertEqual(response.status_code, 302)


# ── CompanyDeleteView ─────────────────────────────────────────────────────────

class CompanyDeleteViewTests(PostViewTestBase):

    def test_deletes_company_and_redirects(self):
        # Create a separate company not linked to any application so deletion succeeds
        company = Company.objects.create(user=self.user, name='Delete Me')
        url = reverse('company_delete', args=[company.pk])
        response = self.client.post(url)
        self.assertRedirects(response, reverse('company_list'))
        self.assertFalse(Company.objects.filter(id=company.id).exists())

    def test_other_users_company_returns_404(self):
        other_company = Company.objects.create(user=self.other_user, name='Other Co')
        url = reverse('company_delete', args=[other_company.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_requires_login(self):
        self.client.logout()
        company = Company.objects.create(user=self.user, name='Delete Me')
        url = reverse('company_delete', args=[company.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)


# ═══════════════════════════════════════════════════════════════════════════════
# GET VIEW TESTS
# ═══════════════════════════════════════════════════════════════════════════════

# ── LandingView ───────────────────────────────────────────────────────────────

class LandingViewTests(PostViewTestBase):

    def test_renders_landing_page(self):
        self.client.logout()
        response = self.client.get(reverse('landing'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'landing.html')

    def test_accessible_without_login(self):
        self.client.logout()
        response = self.client.get(reverse('landing'))
        self.assertEqual(response.status_code, 200)


# ── HomeView ──────────────────────────────────────────────────────────────────

class HomeViewGetTests(PostViewTestBase):

    def test_renders_home_page(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')

    def test_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('home'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('home')}")

    def test_context_contains_application_counts(self):
        response = self.client.get(reverse('home'))
        self.assertIn('total_applications', response.context)
        self.assertIn('total_interviews', response.context)
        self.assertIn('total_in_review', response.context)
        self.assertIn('total_offers', response.context)
        self.assertEqual(response.context['total_applications'], 1)

    def test_context_contains_recent_applications(self):
        response = self.client.get(reverse('home'))
        self.assertIn('recent_applications', response.context)
        self.assertIn(self.application, response.context['recent_applications'])

    def test_context_contains_upcoming_interviews(self):
        response = self.client.get(reverse('home'))
        self.assertIn('upcoming_interviews', response.context)

    def test_context_does_not_include_other_users_data(self):
        other_company = Company.objects.create(user=self.other_user, name='Other Co')
        Application.objects.create(
            user=self.other_user, company=other_company,
            job_title='Other Job', status='applied', date_applied=date.today(),
        )
        response = self.client.get(reverse('home'))
        self.assertEqual(response.context['total_applications'], 1)


# ── TrackerBoardView ──────────────────────────────────────────────────────────

class TrackerBoardViewGetTests(PostViewTestBase):

    def test_renders_tracker_page(self):
        response = self.client.get(reverse('tracker'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tracker/tracker.html')

    def test_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('tracker'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('tracker')}")

    def test_context_has_applications_grouped_by_status(self):
        response = self.client.get(reverse('tracker'))
        for key in ('wishlist', 'applied', 'interviewing', 'offer', 'rejected', 'ghosted', 'follow_up'):
            self.assertIn(key, response.context)
        self.assertIn(self.application, response.context['applied'])

    def test_only_shows_users_applications(self):
        other_company = Company.objects.create(user=self.other_user, name='Other Co')
        other_app = Application.objects.create(
            user=self.other_user, company=other_company,
            job_title='Other Job', status='applied', date_applied=date.today(),
        )
        response = self.client.get(reverse('tracker'))
        self.assertNotIn(other_app, response.context['applied'])


# ── InterviewsView ────────────────────────────────────────────────────────────

class InterviewsViewGetTests(PostViewTestBase):

    def test_renders_interviews_page(self):
        response = self.client.get(reverse('interviews'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tracker/interviews.html')

    def test_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('interviews'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('interviews')}")

    def test_only_shows_interviewing_status_applications(self):
        self.application.status = 'interviewing'
        self.application.save()
        response = self.client.get(reverse('interviews'))
        self.assertIn(self.application, response.context['applications'])

    def test_applied_applications_not_shown(self):
        # application fixture has status='applied'
        response = self.client.get(reverse('interviews'))
        self.assertNotIn(self.application, response.context['applications'])

    def test_context_contains_total_rounds(self):
        response = self.client.get(reverse('interviews'))
        self.assertIn('total_rounds', response.context)


# ── ContactsView ──────────────────────────────────────────────────────────────

class ContactsViewGetTests(PostViewTestBase):

    def test_renders_contacts_page(self):
        response = self.client.get(reverse('contacts'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tracker/contacts.html')

    def test_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('contacts'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('contacts')}")

    def test_shows_users_contacts(self):
        response = self.client.get(reverse('contacts'))
        self.assertIn(self.contact, response.context['contacts'])

    def test_does_not_show_other_users_contacts(self):
        other_contact = Contact.objects.create(user=self.other_user, first_name='Eve')
        response = self.client.get(reverse('contacts'))
        self.assertNotIn(other_contact, response.context['contacts'])


# ── AnalyticsView ─────────────────────────────────────────────────────────────

class AnalyticsViewGetTests(PostViewTestBase):

    def test_renders_analytics_page(self):
        response = self.client.get(reverse('analytics'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tracker/analytics.html')

    def test_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('analytics'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('analytics')}")

    def test_context_contains_stat_keys(self):
        response = self.client.get(reverse('analytics'))
        for key in ('total', 'this_week', 'this_month', 'conversion',
                    'response_rate', 'offer_rate', 'total_interviews', 'funnel'):
            self.assertIn(key, response.context)

    def test_total_reflects_users_applications_only(self):
        other_company = Company.objects.create(user=self.other_user, name='Other Co')
        Application.objects.create(
            user=self.other_user, company=other_company,
            job_title='Other Job', status='applied', date_applied=date.today(),
        )
        response = self.client.get(reverse('analytics'))
        self.assertEqual(response.context['total'], 1)


# ── HelpView ──────────────────────────────────────────────────────────────────

class HelpViewGetTests(PostViewTestBase):

    def test_renders_help_page(self):
        response = self.client.get(reverse('help'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tracker/help.html')

    def test_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('help'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('help')}")


# ── CompanyListView ───────────────────────────────────────────────────────────

class CompanyListViewGetTests(PostViewTestBase):

    def test_renders_company_list(self):
        response = self.client.get(reverse('company_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tracker/company_list.html')

    def test_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('company_list'))
        self.assertEqual(response.status_code, 302)

    def test_shows_users_companies_only(self):
        other_company = Company.objects.create(user=self.other_user, name='Other Co')
        response = self.client.get(reverse('company_list'))
        self.assertIn(self.company, response.context['companies'])
        self.assertNotIn(other_company, response.context['companies'])


# ── CompanyCreateView (GET) ───────────────────────────────────────────────────

class CompanyCreateViewGetTests(PostViewTestBase):

    def test_renders_blank_company_form(self):
        response = self.client.get(reverse('company_add'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tracker/company_form.html')

    def test_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('company_add'))
        self.assertEqual(response.status_code, 302)


# ── CompanyUpdateView (GET) ───────────────────────────────────────────────────

class CompanyUpdateViewGetTests(PostViewTestBase):

    def test_renders_company_form_with_existing_data(self):
        response = self.client.get(reverse('company_edit', args=[self.company.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tracker/company_form.html')
        self.assertContains(response, 'Acme Corp')

    def test_other_users_company_returns_404(self):
        other_company = Company.objects.create(user=self.other_user, name='Other Co')
        response = self.client.get(reverse('company_edit', args=[other_company.pk]))
        self.assertEqual(response.status_code, 404)

    def test_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('company_edit', args=[self.company.pk]))
        self.assertEqual(response.status_code, 302)


# ── CompanyDeleteView (GET) ───────────────────────────────────────────────────

class CompanyDeleteViewGetTests(PostViewTestBase):

    def test_renders_confirm_delete_page(self):
        response = self.client.get(reverse('company_delete', args=[self.company.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tracker/company_confirm_delete.html')

    def test_other_users_company_returns_404(self):
        other_company = Company.objects.create(user=self.other_user, name='Other Co')
        response = self.client.get(reverse('company_delete', args=[other_company.pk]))
        self.assertEqual(response.status_code, 404)

    def test_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('company_delete', args=[self.company.pk]))
        self.assertEqual(response.status_code, 302)


# ── get_job ───────────────────────────────────────────────────────────────────

class GetJobTests(PostViewTestBase):

    def test_returns_job_data_as_json(self):
        response = self.client.get(reverse('get_job', args=[self.application.id]))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['job_title'], 'Developer')
        self.assertEqual(data['company_name'], 'Acme Corp')

    def test_nonexistent_job_returns_404(self):
        response = self.client.get(reverse('get_job', args=[9999]))
        self.assertEqual(response.status_code, 404)


# ── get_interviews ────────────────────────────────────────────────────────────

class GetInterviewsTests(PostViewTestBase):

    def test_returns_interviews_as_json(self):
        response = self.client.get(reverse('get_interviews', args=[self.application.id]))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('interviews', data)
        self.assertEqual(len(data['interviews']), 1)
        self.assertEqual(data['interviews'][0]['interview_type'], 'Human Resources')

    def test_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('get_interviews', args=[self.application.id]))
        self.assertEqual(response.status_code, 302)

    def test_other_users_application_returns_404(self):
        other_company = Company.objects.create(user=self.other_user, name='Other Co')
        other_app = Application.objects.create(
            user=self.other_user, company=other_company,
            job_title='Other Job', status='applied', date_applied=date.today(),
        )
        response = self.client.get(reverse('get_interviews', args=[other_app.id]))
        self.assertEqual(response.status_code, 404)


# ── get_contacts_api ──────────────────────────────────────────────────────────

class GetContactsApiTests(PostViewTestBase):

    def test_returns_contacts_as_json(self):
        response = self.client.get(reverse('get_contacts_api'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('contacts', data)
        self.assertEqual(len(data['contacts']), 1)
        self.assertEqual(data['contacts'][0]['name'], 'Alice Smith')

    def test_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('get_contacts_api'))
        self.assertEqual(response.status_code, 302)

    def test_does_not_return_other_users_contacts(self):
        Contact.objects.create(user=self.other_user, first_name='Eve')
        response = self.client.get(reverse('get_contacts_api'))
        data = response.json()
        names = [c['name'] for c in data['contacts']]
        self.assertNotIn('Eve', names)


# ═══════════════════════════════════════════════════════════════════════════════
# STRIPE / PAYMENT TESTS
# ═══════════════════════════════════════════════════════════════════════════════

# ── payment_success / payment_cancel ─────────────────────────────────────────

class PaymentSuccessViewTests(PostViewTestBase):

    def test_renders_payment_success_page(self):
        response = self.client.get(reverse('payment_success'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'payment_success.html')

    def test_accessible_without_login(self):
        self.client.logout()
        response = self.client.get(reverse('payment_success'))
        self.assertEqual(response.status_code, 200)


class PaymentCancelViewTests(PostViewTestBase):

    def test_renders_payment_cancel_page(self):
        response = self.client.get(reverse('payment_cancel'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'payment_cancel.html')

    def test_accessible_without_login(self):
        self.client.logout()
        response = self.client.get(reverse('payment_cancel'))
        self.assertEqual(response.status_code, 200)


# ── create_checkout_session ───────────────────────────────────────────────────

class CreateCheckoutSessionTests(PostViewTestBase):

    def _mock_session(self, mock_create, url='https://checkout.stripe.com/test'):
        mock_session = MagicMock()
        mock_session.url = url
        mock_create.return_value = mock_session
        return mock_session

    @patch('tracker.views.stripe.checkout.Session.create')
    def test_redirects_to_stripe_checkout_url(self, mock_create):
        self._mock_session(mock_create)
        response = self.client.get(reverse('subscribe'))
        self.assertRedirects(
            response, 'https://checkout.stripe.com/test',
            fetch_redirect_response=False,
        )

    @patch('tracker.views.stripe.checkout.Session.create')
    def test_session_includes_user_id_as_client_reference(self, mock_create):
        self._mock_session(mock_create)
        self.client.get(reverse('subscribe'))
        kwargs = mock_create.call_args[1]
        self.assertEqual(kwargs['client_reference_id'], str(self.user.id))

    @patch('tracker.views.stripe.checkout.Session.create')
    def test_session_includes_user_email(self, mock_create):
        self.user.email = 'testuser@example.com'
        self.user.save()
        self._mock_session(mock_create)
        self.client.get(reverse('subscribe'))
        kwargs = mock_create.call_args[1]
        self.assertEqual(kwargs['customer_email'], 'testuser@example.com')

    @patch('tracker.views.stripe.checkout.Session.create')
    def test_session_uses_subscription_mode(self, mock_create):
        self._mock_session(mock_create)
        self.client.get(reverse('subscribe'))
        kwargs = mock_create.call_args[1]
        self.assertEqual(kwargs['mode'], 'subscription')

    def test_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('subscribe'))
        self.assertEqual(response.status_code, 302)


# ── stripe_webhook ────────────────────────────────────────────────────────────

class StripeWebhookTests(PostViewTestBase):

    WEBHOOK_URL = '/stripe/webhook/'

    def _post_webhook(self, mock_construct, event_type, session_data):
        mock_construct.return_value = {
            'type': event_type,
            'data': {'object': session_data},
        }
        return self.client.post(
            self.WEBHOOK_URL,
            data='{}',
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='test_sig',
        )

    @patch('tracker.views.stripe.Webhook.construct_event')
    def test_checkout_completed_grants_premium(self, mock_construct):
        response = self._post_webhook(
            mock_construct,
            'checkout.session.completed',
            {'client_reference_id': str(self.user.id), 'customer': 'cus_test123'},
        )
        self.assertEqual(response.status_code, 200)
        self.user.profile.refresh_from_db()
        self.assertTrue(self.user.profile.is_premium)

    @patch('tracker.views.stripe.Webhook.construct_event')
    def test_checkout_completed_saves_stripe_customer_id(self, mock_construct):
        self._post_webhook(
            mock_construct,
            'checkout.session.completed',
            {'client_reference_id': str(self.user.id), 'customer': 'cus_test123'},
        )
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.stripe_customer_id, 'cus_test123')

    @patch('tracker.views.stripe.Webhook.construct_event')
    def test_checkout_completed_unknown_user_returns_200(self, mock_construct):
        response = self._post_webhook(
            mock_construct,
            'checkout.session.completed',
            {'client_reference_id': '9999', 'customer': 'cus_test123'},
        )
        self.assertEqual(response.status_code, 200)

    @patch('tracker.views.stripe.Webhook.construct_event')
    def test_unhandled_event_type_returns_200_without_granting_premium(self, mock_construct):
        response = self._post_webhook(
            mock_construct,
            'customer.subscription.deleted',
            {'client_reference_id': str(self.user.id)},
        )
        self.assertEqual(response.status_code, 200)
        self.user.profile.refresh_from_db()
        self.assertFalse(self.user.profile.is_premium)

    @patch('tracker.views.stripe.Webhook.construct_event')
    def test_webhook_accessible_without_login(self, mock_construct):
        self.client.logout()
        response = self._post_webhook(
            mock_construct,
            'checkout.session.completed',
            {'client_reference_id': str(self.user.id), 'customer': 'cus_test123'},
        )
        self.assertEqual(response.status_code, 200)


# ═══════════════════════════════════════════════════════════════════════════════
# DOCUMENTS TESTS
# ═══════════════════════════════════════════════════════════════════════════════

def _fake_file():
    return SimpleUploadedFile('cv.pdf', b'%PDF-1.4 fake content', content_type='application/pdf')


# ── DocumentsView ─────────────────────────────────────────────────────────────

class DocumentsViewGetTests(PostViewTestBase):

    def test_renders_documents_page(self):
        response = self.client.get(reverse('documents'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tracker/documents.html')

    def test_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('documents'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('documents')}")

    @patch('cloudinary.uploader.upload')
    def test_shows_users_documents(self, mock_upload):
        mock_upload.return_value = {'public_id': 'docs/cv1', 'version': 1, 'resource_type': 'raw', 'type': 'upload'}
        doc = Document.objects.create(user=self.user, name='My CV', file=_fake_file(), file_type='cv')
        response = self.client.get(reverse('documents'))
        self.assertIn(doc, response.context['documents'])

    @patch('cloudinary.uploader.upload')
    def test_does_not_show_other_users_documents(self, mock_upload):
        mock_upload.return_value = {'public_id': 'docs/other', 'version': 1, 'resource_type': 'raw', 'type': 'upload'}
        other_doc = Document.objects.create(user=self.other_user, name='Other CV', file=_fake_file(), file_type='cv')
        response = self.client.get(reverse('documents'))
        self.assertNotIn(other_doc, response.context['documents'])


# ── upload_document ───────────────────────────────────────────────────────────

class UploadDocumentTests(PostViewTestBase):

    def test_requires_login(self):
        self.client.logout()
        response = self.client.post(reverse('upload_document'), {'name': 'CV', 'file': _fake_file()})
        self.assertEqual(response.status_code, 302)

    def test_no_file_returns_400(self):
        response = self.client.post(reverse('upload_document'), {'name': 'CV'})
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content, {'success': False, 'error': 'No file provided'})

    def test_no_name_returns_400(self):
        response = self.client.post(reverse('upload_document'), {'name': '', 'file': _fake_file()})
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content, {'success': False, 'error': 'Name is required'})

    @patch('cloudinary.uploader.upload')
    def test_valid_upload_creates_document(self, mock_upload):
        mock_upload.return_value = {'public_id': 'docs/cv1', 'version': 1, 'resource_type': 'raw', 'type': 'upload'}
        response = self.client.post(
            reverse('upload_document'),
            {'name': 'My CV', 'file_type': 'cv', 'file': _fake_file()},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertTrue(Document.objects.filter(name='My CV', user=self.user).exists())

    @patch('cloudinary.uploader.upload')
    def test_valid_upload_returns_document_fields(self, mock_upload):
        mock_upload.return_value = {'public_id': 'docs/cv1', 'version': 1, 'resource_type': 'raw', 'type': 'upload'}
        response = self.client.post(
            reverse('upload_document'),
            {'name': 'Portfolio', 'file_type': 'portfolio', 'file': _fake_file()},
        )
        data = response.json()
        self.assertIn('id', data)
        self.assertEqual(data['name'], 'Portfolio')
        self.assertIn('url', data)
        self.assertIn('created_at', data)


# ── delete_document ───────────────────────────────────────────────────────────

class DeleteDocumentTests(PostViewTestBase):

    @patch('cloudinary.uploader.upload')
    def setUp(self, mock_upload):
        mock_upload.return_value = {'public_id': 'docs/cv1', 'version': 1, 'resource_type': 'raw', 'type': 'upload'}
        super().setUp()
        self.doc = Document.objects.create(user=self.user, name='My CV', file=_fake_file(), file_type='cv')

    def test_deletes_document_and_returns_success(self):
        url = reverse('delete_document', args=[self.doc.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'success': True})
        self.assertFalse(Document.objects.filter(id=self.doc.id).exists())

    def test_get_returns_400(self):
        url = reverse('delete_document', args=[self.doc.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

    def test_requires_login(self):
        self.client.logout()
        url = reverse('delete_document', args=[self.doc.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

    @patch('cloudinary.uploader.upload')
    def test_other_users_document_returns_404(self, mock_upload):
        mock_upload.return_value = {'public_id': 'docs/other', 'version': 1, 'resource_type': 'raw', 'type': 'upload'}
        other_doc = Document.objects.create(user=self.other_user, name='Other CV', file=_fake_file(), file_type='cv')
        url = reverse('delete_document', args=[other_doc.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)


# ── get_documents_api ─────────────────────────────────────────────────────────

class GetDocumentsApiTests(PostViewTestBase):

    @patch('cloudinary.uploader.upload')
    def setUp(self, mock_upload):
        mock_upload.return_value = {'public_id': 'docs/cv1', 'version': 1, 'resource_type': 'raw', 'type': 'upload'}
        super().setUp()
        self.doc = Document.objects.create(user=self.user, name='My CV', file=_fake_file(), file_type='cv')

    def test_returns_documents_as_json(self):
        response = self.client.get(reverse('get_documents_api'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('documents', data)
        self.assertEqual(len(data['documents']), 1)
        self.assertEqual(data['documents'][0]['name'], 'My CV')

    def test_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('get_documents_api'))
        self.assertEqual(response.status_code, 302)

    @patch('cloudinary.uploader.upload')
    def test_does_not_return_other_users_documents(self, mock_upload):
        mock_upload.return_value = {'public_id': 'docs/other', 'version': 1, 'resource_type': 'raw', 'type': 'upload'}
        Document.objects.create(user=self.other_user, name='Other CV', file=_fake_file(), file_type='cv')
        response = self.client.get(reverse('get_documents_api'))
        data = response.json()
        names = [d['name'] for d in data['documents']]
        self.assertNotIn('Other CV', names)


# ── update_job_documents ──────────────────────────────────────────────────────

class UpdateJobDocumentsTests(PostViewTestBase):

    @patch('cloudinary.uploader.upload')
    def setUp(self, mock_upload):
        mock_upload.return_value = {'public_id': 'docs/cv1', 'version': 1, 'resource_type': 'raw', 'type': 'upload'}
        super().setUp()
        self.doc = Document.objects.create(user=self.user, name='My CV', file=_fake_file(), file_type='cv')

    def test_sets_documents_on_application(self):
        url = reverse('update_job_documents', args=[self.application.id])
        response = self._json_post(url, {'document_ids': [self.doc.id]})
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'success': True})
        self.assertIn(self.doc, self.application.documents.all())

    def test_clears_documents_when_empty_list(self):
        self.application.documents.add(self.doc)
        url = reverse('update_job_documents', args=[self.application.id])
        response = self._json_post(url, {'document_ids': []})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.application.documents.count(), 0)

    def test_requires_login(self):
        self.client.logout()
        url = reverse('update_job_documents', args=[self.application.id])
        response = self._json_post(url, {'document_ids': []})
        self.assertEqual(response.status_code, 302)

    def test_other_users_application_returns_404(self):
        other_company = Company.objects.create(user=self.other_user, name='Other Co')
        other_app = Application.objects.create(
            user=self.other_user, company=other_company,
            job_title='Other Job', status='applied', date_applied=date.today(),
        )
        url = reverse('update_job_documents', args=[other_app.id])
        response = self._json_post(url, {'document_ids': []})
        self.assertEqual(response.status_code, 404)

    def test_get_returns_400(self):
        url = reverse('update_job_documents', args=[self.application.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)


# ── HomeView Notifications ─────────────────────────────────────────────────────

class HomeViewNotificationsTests(PostViewTestBase):
    """Tests for the notification context data generated by HomeView."""

    def setUp(self):
        super().setUp()
        # Push the shared setUp interview well into the future so it never
        # accidentally falls inside the 3-day upcoming-interview window.
        self.interview.date = timezone.now() + timedelta(days=30)
        self.interview.save()

    # ── helpers ──────────────────────────────────────────────────────────────

    def _notifications(self):
        return self.client.get(reverse('home')).context['notifications']

    def _total(self):
        return self.client.get(reverse('home')).context['total_notifications']

    # ── Context keys ──────────────────────────────────────────────────────────

    def test_context_contains_notifications_keys(self):
        response = self.client.get(reverse('home'))
        self.assertIn('notifications', response.context)
        self.assertIn('total_notifications', response.context)

    # ── Upcoming interviews ───────────────────────────────────────────────────

    def test_interview_within_3_days_generates_teal_notification(self):
        Interview.objects.create(
            application=self.application,
            interview_type='Technical Interview',
            date=timezone.now() + timedelta(hours=36),
        )
        teal = [n for n in self._notifications() if n['color'] == 'teal']
        self.assertEqual(len(teal), 1)
        self.assertEqual(teal[0]['title'], self.company.name)

    def test_interview_beyond_3_days_excluded(self):
        Interview.objects.create(
            application=self.application,
            interview_type='Technical Interview',
            date=timezone.now() + timedelta(days=5),
        )
        teal = [n for n in self._notifications() if n['color'] == 'teal']
        self.assertEqual(len(teal), 0)

    def test_past_interview_excluded(self):
        Interview.objects.create(
            application=self.application,
            interview_type='Technical Interview',
            date=timezone.now() - timedelta(hours=1),
        )
        teal = [n for n in self._notifications() if n['color'] == 'teal']
        self.assertEqual(len(teal), 0)

    def test_interview_today_has_high_urgency(self):
        Interview.objects.create(
            application=self.application,
            interview_type='Human Resources',
            date=timezone.now() + timedelta(hours=2),
        )
        teal = [n for n in self._notifications() if n['color'] == 'teal']
        self.assertEqual(teal[0]['urgency'], 'high')

    def test_interview_in_2_days_has_medium_urgency(self):
        Interview.objects.create(
            application=self.application,
            interview_type='Human Resources',
            date=timezone.now() + timedelta(days=2),
        )
        teal = [n for n in self._notifications() if n['color'] == 'teal']
        self.assertEqual(teal[0]['urgency'], 'medium')

    # ── Stale applied applications ────────────────────────────────────────────

    def test_applied_5_days_ago_generates_blue_notification(self):
        Application.objects.create(
            user=self.user, company=self.company,
            job_title='Stale Job', status='applied',
            date_applied=date.today() - timedelta(days=6),
        )
        blue = [n for n in self._notifications() if n['color'] == 'blue']
        self.assertEqual(len(blue), 1)
        self.assertIn('follow-up', blue[0]['text'])

    def test_applied_today_not_stale(self):
        # setUp application has date_applied=today — must not appear
        blue = [n for n in self._notifications() if n['color'] == 'blue']
        self.assertEqual(len(blue), 0)

    def test_applied_4_days_ago_not_stale(self):
        Application.objects.create(
            user=self.user, company=self.company,
            job_title='Recent Job', status='applied',
            date_applied=date.today() - timedelta(days=4),
        )
        blue = [n for n in self._notifications() if n['color'] == 'blue']
        self.assertEqual(len(blue), 0)

    def test_stale_applied_notification_has_medium_urgency(self):
        Application.objects.create(
            user=self.user, company=self.company,
            job_title='Stale Job', status='applied',
            date_applied=date.today() - timedelta(days=7),
        )
        blue = [n for n in self._notifications() if n['color'] == 'blue']
        self.assertEqual(blue[0]['urgency'], 'medium')

    # ── Wishlist reminders ────────────────────────────────────────────────────

    def test_wishlist_14_days_old_generates_purple_notification(self):
        Application.objects.create(
            user=self.user, company=self.company,
            job_title='Wishlist Job', status='wishlist',
            date_applied=date.today() - timedelta(days=15),
        )
        purple = [n for n in self._notifications() if n['color'] == 'purple']
        self.assertEqual(len(purple), 1)
        self.assertIn('apply', purple[0]['text'])

    def test_wishlist_recent_excluded(self):
        Application.objects.create(
            user=self.user, company=self.company,
            job_title='New Wishlist', status='wishlist',
            date_applied=date.today() - timedelta(days=5),
        )
        purple = [n for n in self._notifications() if n['color'] == 'purple']
        self.assertEqual(len(purple), 0)

    def test_wishlist_notification_has_low_urgency(self):
        Application.objects.create(
            user=self.user, company=self.company,
            job_title='Wishlist Job', status='wishlist',
            date_applied=date.today() - timedelta(days=20),
        )
        purple = [n for n in self._notifications() if n['color'] == 'purple']
        self.assertEqual(purple[0]['urgency'], 'low')

    # ── Pending offers ────────────────────────────────────────────────────────

    def test_offer_application_generates_green_notification(self):
        Application.objects.create(
            user=self.user, company=self.company,
            job_title='Great Job', status='offer',
            date_applied=date.today(),
        )
        green = [n for n in self._notifications() if n['color'] == 'green']
        self.assertEqual(len(green), 1)

    def test_offer_notification_has_high_urgency(self):
        Application.objects.create(
            user=self.user, company=self.company,
            job_title='Great Job', status='offer',
            date_applied=date.today(),
        )
        green = [n for n in self._notifications() if n['color'] == 'green']
        self.assertEqual(green[0]['urgency'], 'high')

    # ── Total count & empty state ─────────────────────────────────────────────

    def test_total_notifications_matches_list_length(self):
        Application.objects.create(
            user=self.user, company=self.company,
            job_title='Offer Job', status='offer', date_applied=date.today(),
        )
        Application.objects.create(
            user=self.user, company=self.company,
            job_title='Stale Job', status='applied',
            date_applied=date.today() - timedelta(days=6),
        )
        response = self.client.get(reverse('home'))
        self.assertEqual(
            response.context['total_notifications'],
            len(response.context['notifications']),
        )

    def test_zero_notifications_when_none_qualify(self):
        # setUp: applied today (not stale), no upcoming interviews (<30d), no offers
        self.assertEqual(self._notifications(), [])
        self.assertEqual(self._total(), 0)

    # ── User isolation ────────────────────────────────────────────────────────

    def test_other_users_offer_not_included(self):
        other_company = Company.objects.create(user=self.other_user, name='Other Co')
        Application.objects.create(
            user=self.other_user, company=other_company,
            job_title='Offer Job', status='offer', date_applied=date.today(),
        )
        green = [n for n in self._notifications() if n['color'] == 'green']
        self.assertEqual(len(green), 0)

    def test_other_users_stale_application_not_included(self):
        other_company = Company.objects.create(user=self.other_user, name='Other Co')
        Application.objects.create(
            user=self.other_user, company=other_company,
            job_title='Stale Job', status='applied',
            date_applied=date.today() - timedelta(days=10),
        )
        blue = [n for n in self._notifications() if n['color'] == 'blue']
        self.assertEqual(len(blue), 0)
