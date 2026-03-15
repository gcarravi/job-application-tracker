# Trackwise – Testing Documentation

This document covers all testing carried out on the Trackwise application, including automated tests, manual functional testing, and validation.

---

## Table of Contents

- [Running the Automated Tests](#running-the-automated-tests)
- [Automated Tests](#automated-tests)
  - [ApplicationForm Tests](#applicationform-tests)
  - [RegisterForm Tests](#registerform-tests)
  - [Register View Tests](#register-view-tests)
  - [Upload Photo View Tests](#upload-photo-view-tests)
  - [Tracker GET View Tests](#tracker-get-view-tests)
  - [Tracker POST View Tests](#tracker-post-view-tests)
  - [Stripe Payment Tests](#stripe-payment-tests)
- [Manual Testing](#manual-testing)
  - [Authentication](#authentication)
  - [Job Tracker Board](#job-tracker-board)
  - [Interview Management](#interview-management)
  - [Company Management](#company-management)
  - [Contacts Directory](#contacts-directory)
  - [Analytics Page](#analytics-page)
  - [Help & Support Page](#help--support-page)
  - [Subscription & Payments](#subscription--payments)
- [Validation](#validation)
  - [HTML Validation](#html-validation)
  - [CSS Validation](#css-validation)
  - [JavaScript Validation](#javascript-validation)
  - [Python Linting](#python-linting)
- [Browser Compatibility](#browser-compatibility)
- [Responsiveness Testing](#responsiveness-testing)
- [Known Issues](#known-issues)

---

## Running the Automated Tests

To run all automated tests:

```bash
python manage.py test
```

To run a specific test module:

```bash
python manage.py test tracker.test_forms
python manage.py test accounts.test_forms
```

To run with verbose output:

```bash
python manage.py test --verbosity=2
```

**Current result:** 120 tests, 0 failures, 0 errors.

To run only view tests:

```bash
python manage.py test tracker.test_views
python manage.py test accounts.test_views
```

To run only form tests:

```bash
python manage.py test tracker.test_forms
python manage.py test accounts.test_forms
```

---

## Automated Tests

### ApplicationForm Tests

**File:** `tracker/test_forms.py`

The `ApplicationForm` is a ModelForm that handles job application creation. It includes custom fields for company details and a custom `save()` method that creates or retrieves a Company record.

#### Validation Tests (`ApplicationFormValidationTests`)

| Test | Description | Expected Result | Pass/Fail |
|------|-------------|-----------------|-----------|
| `test_valid_form` | All required fields provided | Form is valid | ✅ Pass |
| `test_missing_company_name` | `company_name` left blank | Form invalid, error on `company_name` | ✅ Pass |
| `test_missing_job_title` | `job_title` left blank | Form invalid, error on `job_title` | ✅ Pass |
| `test_missing_status` | `status` left blank | Form invalid, error on `status` | ✅ Pass |
| `test_missing_date_applied` | `date_applied` left blank | Form invalid, error on `date_applied` | ✅ Pass |
| `test_company_location_not_required` | `company_location` left blank | Form is valid | ✅ Pass |
| `test_company_website_not_required` | `company_website` left blank | Form is valid | ✅ Pass |
| `test_salary_range_not_required` | `salary_range` left blank | Form is valid | ✅ Pass |
| `test_notes_not_required` | `notes` left blank | Form is valid | ✅ Pass |
| `test_invalid_website_url` | `company_website` set to `"not-a-url"` | Form invalid, error on `company_website` | ✅ Pass |
| `test_invalid_status_choice` | `status` set to an unlisted value | Form invalid, error on `status` | ✅ Pass |
| `test_invalid_date_format` | `date_applied` set to `"not-a-date"` | Form invalid, error on `date_applied` | ✅ Pass |

#### Structure Tests (`ApplicationFormStructureTests`)

| Test | Description | Expected Result | Pass/Fail |
|------|-------------|-----------------|-----------|
| `test_field_order` | Field order matches design spec | Fields appear in: company_name, company_location, company_website, job_title, salary_range, status, date_applied, notes | ✅ Pass |
| `test_all_fields_have_form_control_class` | All field widgets have Bootstrap class | Every field widget has `form-control` in its class attribute | ✅ Pass |
| `test_form_initialises_without_user` | Form created without `user` kwarg | No exception raised; `form.user` is `None` | ✅ Pass |
| `test_date_applied_uses_date_input_widget` | `date_applied` uses correct widget | Widget is an instance of `DateInput` | ✅ Pass |

#### Save Tests (`ApplicationFormSaveTests`)

These tests mirror the view pattern where `form.save(commit=False)` is called, `application.user` is set manually, then `application.save()` is called.

| Test | Description | Expected Result | Pass/Fail |
|------|-------------|-----------------|-----------|
| `test_save_creates_application` | Form saved with valid data | Returns an `Application` instance with correct `job_title` and `status` | ✅ Pass |
| `test_save_creates_company` | Form saved with a new company name | A `Company` record is created for the user | ✅ Pass |
| `test_save_company_uses_provided_location_and_website` | Company details provided | Company has correct `location` and `website` | ✅ Pass |
| `test_save_links_application_to_company` | Application saved | Application's `company.name` matches the submitted company name | ✅ Pass |
| `test_save_reuses_existing_company` | Same company name submitted twice | Only one Company record exists (uses `get_or_create`) | ✅ Pass |
| `test_save_without_commit_does_not_persist` | `save(commit=False)` called | Application has no `pk`; database count is 0 | ✅ Pass |
| `test_save_persists_to_database` | `save()` called normally | One Application record exists in the database | ✅ Pass |
| `test_save_application_has_correct_user_via_company` | Application saved with user | `application.company.user` equals the logged-in user | ✅ Pass |

---

### RegisterForm Tests

**File:** `accounts/test_forms.py`

The `RegisterForm` extends Django's built-in `UserCreationForm` with a required `email` field.

#### Validation Tests (`RegisterFormValidationTests`)

| Test | Description | Expected Result | Pass/Fail |
|------|-------------|-----------------|-----------|
| `test_valid_form` | All fields valid | Form is valid | ✅ Pass |
| `test_missing_username` | `username` left blank | Form invalid, error on `username` | ✅ Pass |
| `test_missing_email` | `email` left blank | Form invalid, error on `email` | ✅ Pass |
| `test_invalid_email_format` | `email` set to `"not-an-email"` | Form invalid, error on `email` | ✅ Pass |
| `test_password_mismatch` | `password1` and `password2` differ | Form invalid, error on `password2` | ✅ Pass |
| `test_missing_password1` | `password1` left blank | Form invalid, error on `password1` | ✅ Pass |
| `test_missing_password2` | `password2` left blank | Form invalid, error on `password2` | ✅ Pass |
| `test_duplicate_username` | Username already taken | Form invalid, error on `username` | ✅ Pass |
| `test_password_too_short` | Password under 8 characters | Form invalid, error on `password2` | ✅ Pass |
| `test_entirely_numeric_password` | Password is all numbers (`12345678`) | Form invalid (Django password validators) | ✅ Pass |

#### Structure Tests (`RegisterFormStructureTests`)

| Test | Description | Expected Result | Pass/Fail |
|------|-------------|-----------------|-----------|
| `test_email_field_is_present` | Form contains an `email` field | `email` in `form.fields` | ✅ Pass |
| `test_email_field_is_required` | Email field is not optional | `form.fields['email'].required` is `True` | ✅ Pass |
| `test_expected_fields_present` | All four fields exist | `username`, `email`, `password1`, `password2` all in `form.fields` | ✅ Pass |

---

### Register View Tests

**File:** `accounts/test_views.py`

The `register` view handles account creation and automatically logs in the new user on success.

#### `RegisterViewTests`

| Test | Description | Expected Result | Pass/Fail |
|------|-------------|-----------------|-----------|
| `test_valid_registration_creates_user` | Valid form submitted | User record created in database | ✅ Pass |
| `test_valid_registration_logs_user_in` | Valid form submitted | User is authenticated immediately after registration | ✅ Pass |
| `test_valid_registration_redirects_to_home` | Valid form submitted | Redirects to `/home/` | ✅ Pass |
| `test_mismatched_passwords_rerenders_form` | `password1 ≠ password2` | Form re-rendered with errors; no user created | ✅ Pass |
| `test_missing_email_rerenders_form` | `email` left blank | Form re-rendered with errors; no user created | ✅ Pass |
| `test_duplicate_username_rerenders_form` | Username already taken | Form re-rendered; only one user record exists | ✅ Pass |
| `test_get_renders_blank_form` | GET request | Register page rendered with a blank form | ✅ Pass |

---

### Upload Photo View Tests

**File:** `accounts/test_views.py`

The `upload_photo` view handles profile photo uploads, saving the file to Cloudinary and returning the resulting URL. Cloudinary API calls are mocked with `unittest.mock.patch` so no real network requests are made during testing.

#### `UploadPhotoViewTests`

| Test | Description | Expected Result | Pass/Fail |
|------|-------------|-----------------|-----------|
| `test_requires_login` | POST while logged out | Redirects to login | ✅ Pass |
| `test_no_file_returns_400` | POST with no file attached | Returns 400 with `{"success": false, "error": "No file provided"}` | ✅ Pass |
| `test_valid_upload_returns_success` | POST with a JPEG file (Cloudinary mocked) | Returns 200 with `{"success": true, "url": "..."}` | ✅ Pass |
| `test_valid_upload_saves_photo_to_profile` | POST with a JPEG file (Cloudinary mocked) | `profile.photo` is set and truthy after save | ✅ Pass |

---

### Tracker GET View Tests

**File:** `tracker/test_views.py`

Tests for all GET-only views and API endpoints across the tracker app. All authenticated views are tested for login enforcement and data isolation between users.

#### `LandingViewTests`

| Test | Description | Expected Result | Pass/Fail |
|------|-------------|-----------------|-----------|
| `test_renders_landing_page` | GET `/` | Returns 200 with `landing.html` | ✅ Pass |
| `test_accessible_without_login` | GET `/` while logged out | Returns 200 (public page) | ✅ Pass |

#### `HomeViewGetTests`

| Test | Description | Expected Result | Pass/Fail |
|------|-------------|-----------------|-----------|
| `test_renders_home_page` | GET `/home/` | Returns 200 with `home.html` | ✅ Pass |
| `test_requires_login` | GET `/home/` while logged out | Redirects to login | ✅ Pass |
| `test_context_contains_application_counts` | GET `/home/` | Context contains `total_applications`, `total_interviews`, `total_in_review`, `total_offers` | ✅ Pass |
| `test_context_contains_recent_applications` | GET `/home/` | Context contains `recent_applications` including the user's application | ✅ Pass |
| `test_context_contains_upcoming_interviews` | GET `/home/` | Context contains `upcoming_interviews` | ✅ Pass |
| `test_context_does_not_include_other_users_data` | Second user has applications | `total_applications` is 1 (own data only) | ✅ Pass |

#### `TrackerBoardViewGetTests`

| Test | Description | Expected Result | Pass/Fail |
|------|-------------|-----------------|-----------|
| `test_renders_tracker_page` | GET `/tracker/` | Returns 200 with `tracker/tracker.html` | ✅ Pass |
| `test_requires_login` | GET `/tracker/` while logged out | Redirects to login | ✅ Pass |
| `test_context_has_applications_grouped_by_status` | GET `/tracker/` | Context has all 7 status keys; application in correct column | ✅ Pass |
| `test_only_shows_users_applications` | Second user has applications | Other user's applications not in context | ✅ Pass |

#### `InterviewsViewGetTests`

| Test | Description | Expected Result | Pass/Fail |
|------|-------------|-----------------|-----------|
| `test_renders_interviews_page` | GET `/interviews/` | Returns 200 with `tracker/interviews.html` | ✅ Pass |
| `test_requires_login` | GET `/interviews/` while logged out | Redirects to login | ✅ Pass |
| `test_only_shows_interviewing_status_applications` | Application set to `interviewing` | Application appears in context | ✅ Pass |
| `test_applied_applications_not_shown` | Application has status `applied` | Application not in context | ✅ Pass |
| `test_context_contains_total_rounds` | GET `/interviews/` | Context contains `total_rounds` | ✅ Pass |

#### `ContactsViewGetTests`

| Test | Description | Expected Result | Pass/Fail |
|------|-------------|-----------------|-----------|
| `test_renders_contacts_page` | GET `/contacts/` | Returns 200 with `tracker/contacts.html` | ✅ Pass |
| `test_requires_login` | GET `/contacts/` while logged out | Redirects to login | ✅ Pass |
| `test_shows_users_contacts` | User has a contact | Contact appears in context | ✅ Pass |
| `test_does_not_show_other_users_contacts` | Second user has a contact | Other user's contact not in context | ✅ Pass |

#### `AnalyticsViewGetTests`

| Test | Description | Expected Result | Pass/Fail |
|------|-------------|-----------------|-----------|
| `test_renders_analytics_page` | GET `/analytics/` | Returns 200 with `tracker/analytics.html` | ✅ Pass |
| `test_requires_login` | GET `/analytics/` while logged out | Redirects to login | ✅ Pass |
| `test_context_contains_stat_keys` | GET `/analytics/` | Context contains `total`, `this_week`, `this_month`, `conversion`, `response_rate`, `offer_rate`, `total_interviews`, `funnel` | ✅ Pass |
| `test_total_reflects_users_applications_only` | Second user has applications | `total` is 1 (own data only) | ✅ Pass |

#### `HelpViewGetTests`

| Test | Description | Expected Result | Pass/Fail |
|------|-------------|-----------------|-----------|
| `test_renders_help_page` | GET `/help/` | Returns 200 with `tracker/help.html` | ✅ Pass |
| `test_requires_login` | GET `/help/` while logged out | Redirects to login | ✅ Pass |

#### `CompanyListViewGetTests`

| Test | Description | Expected Result | Pass/Fail |
|------|-------------|-----------------|-----------|
| `test_renders_company_list` | GET `/companies/` | Returns 200 with `tracker/company_list.html` | ✅ Pass |
| `test_requires_login` | GET `/companies/` while logged out | Redirects to login | ✅ Pass |
| `test_shows_users_companies_only` | Second user has a company | Own company in context; other user's company not in context | ✅ Pass |

#### `CompanyCreateViewGetTests`

| Test | Description | Expected Result | Pass/Fail |
|------|-------------|-----------------|-----------|
| `test_renders_blank_company_form` | GET `/companies/add/` | Returns 200 with `tracker/company_form.html` | ✅ Pass |
| `test_requires_login` | GET `/companies/add/` while logged out | Redirects to login | ✅ Pass |

#### `CompanyUpdateViewGetTests`

| Test | Description | Expected Result | Pass/Fail |
|------|-------------|-----------------|-----------|
| `test_renders_company_form_with_existing_data` | GET `/companies/<pk>/edit/` | Returns 200; response contains company name | ✅ Pass |
| `test_other_users_company_returns_404` | GET edit URL for another user's company | Returns 404 | ✅ Pass |
| `test_requires_login` | GET while logged out | Redirects to login | ✅ Pass |

#### `CompanyDeleteViewGetTests`

| Test | Description | Expected Result | Pass/Fail |
|------|-------------|-----------------|-----------|
| `test_renders_confirm_delete_page` | GET `/companies/<pk>/delete/` | Returns 200 with `tracker/company_confirm_delete.html` | ✅ Pass |
| `test_other_users_company_returns_404` | GET delete URL for another user's company | Returns 404 | ✅ Pass |
| `test_requires_login` | GET while logged out | Redirects to login | ✅ Pass |

#### `GetJobTests`

| Test | Description | Expected Result | Pass/Fail |
|------|-------------|-----------------|-----------|
| `test_returns_job_data_as_json` | GET `/get-job/<id>/` | Returns 200 with `job_title` and `company_name` | ✅ Pass |
| `test_nonexistent_job_returns_404` | GET with unknown ID | Returns 404 | ✅ Pass |

#### `GetInterviewsTests`

| Test | Description | Expected Result | Pass/Fail |
|------|-------------|-----------------|-----------|
| `test_returns_interviews_as_json` | GET `/get-interviews/<app_id>/` | Returns 200 with `interviews` list | ✅ Pass |
| `test_requires_login` | GET while logged out | Redirects to login | ✅ Pass |
| `test_other_users_application_returns_404` | GET interviews for another user's application | Returns 404 | ✅ Pass |

#### `GetContactsApiTests`

| Test | Description | Expected Result | Pass/Fail |
|------|-------------|-----------------|-----------|
| `test_returns_contacts_as_json` | GET `/contacts/api/` | Returns 200 with `contacts` list | ✅ Pass |
| `test_requires_login` | GET while logged out | Redirects to login | ✅ Pass |
| `test_does_not_return_other_users_contacts` | Second user has a contact | Other user's contact not in response | ✅ Pass |

---

### Tracker POST View Tests

**File:** `tracker/test_views.py`

Tests for all POST endpoints. JSON endpoints are tested with `content_type='application/json'`. All `@login_required` views are tested for authentication enforcement and cross-user access control.

#### `HomeViewPostTests`

| Test | Description | Expected Result | Pass/Fail |
|------|-------------|-----------------|-----------|
| `test_valid_form_creates_application_and_redirects_to_tracker` | Valid form POST to `/home/` | Application created; redirects to `/tracker/` | ✅ Pass |
| `test_invalid_form_rerenders_home` | Missing required fields | Re-renders `home.html` with errors | ✅ Pass |
| `test_requires_login` | POST while logged out | Redirects to login | ✅ Pass |

#### `TrackerBoardViewPostTests`

| Test | Description | Expected Result | Pass/Fail |
|------|-------------|-----------------|-----------|
| `test_valid_form_creates_application_and_redirects` | Valid form POST to `/tracker/` | Application created; redirects to `/tracker/` | ✅ Pass |
| `test_invalid_form_rerenders_tracker` | Missing required fields | Re-renders `tracker/tracker.html` with errors | ✅ Pass |
| `test_requires_login` | POST while logged out | Redirects to login | ✅ Pass |

#### `DeleteJobTests`

| Test | Description | Expected Result | Pass/Fail |
|------|-------------|-----------------|-----------|
| `test_deletes_job_and_returns_success` | POST `/delete-job/<id>/` | Application deleted; returns `{"success": true}` | ✅ Pass |
| `test_get_returns_400` | GET request | Returns 400 | ✅ Pass |
| `test_nonexistent_job_returns_404` | POST with unknown ID | Returns 404 | ✅ Pass |

#### `UpdateJobStatusTests`

| Test | Description | Expected Result | Pass/Fail |
|------|-------------|-----------------|-----------|
| `test_updates_status_and_returns_success` | Valid status in JSON body | Status updated; returns `{"success": true}` | ✅ Pass |
| `test_invalid_status_returns_400` | Unknown status value | Returns 400 | ✅ Pass |
| `test_nonexistent_job_returns_404` | Unknown job ID | Returns 404 | ✅ Pass |
| `test_invalid_json_returns_400` | Malformed request body | Returns 400 | ✅ Pass |
| `test_get_returns_400` | GET request | Returns 400 | ✅ Pass |

#### `UpdateJobTests`

| Test | Description | Expected Result | Pass/Fail |
|------|-------------|-----------------|-----------|
| `test_updates_job_fields` | `job_title` and `salary_range` in body | Fields updated on application | ✅ Pass |
| `test_sets_recruiter` | `recruiter_id` in body | Recruiter linked to application | ✅ Pass |
| `test_clears_recruiter_when_empty` | `recruiter_id` set to `""` | Recruiter cleared | ✅ Pass |
| `test_get_returns_400` | GET request | Returns 400 | ✅ Pass |
| `test_nonexistent_job_returns_404` | Unknown job ID | Returns 404 | ✅ Pass |

#### `SaveInterviewTests`

| Test | Description | Expected Result | Pass/Fail |
|------|-------------|-----------------|-----------|
| `test_creates_interview_and_returns_id` | Valid JSON body with date | Interview created; `id` returned | ✅ Pass |
| `test_missing_date_returns_400` | No `date` field | Returns 400 | ✅ Pass |
| `test_invalid_date_returns_400` | Unparseable date string | Returns 400 | ✅ Pass |
| `test_sets_interviewers` | `interviewer_ids` in body | Interviewers linked to interview | ✅ Pass |
| `test_get_returns_400` | GET request | Returns 400 | ✅ Pass |
| `test_requires_login` | POST while logged out | Redirects to login | ✅ Pass |
| `test_other_users_application_returns_404` | Application belongs to another user | Returns 404 | ✅ Pass |

#### `UpdateInterviewTests`

| Test | Description | Expected Result | Pass/Fail |
|------|-------------|-----------------|-----------|
| `test_updates_interview_fields` | `interview_type`, `date`, `result`, `notes` in body | Fields updated | ✅ Pass |
| `test_updates_interviewers` | `interviewer_ids` in body | Interviewers updated | ✅ Pass |
| `test_get_returns_400` | GET request | Returns 400 | ✅ Pass |
| `test_requires_login` | POST while logged out | Redirects to login | ✅ Pass |
| `test_other_users_interview_returns_404` | Interview belongs to another user | Returns 404 | ✅ Pass |

#### `DeleteInterviewTests`

| Test | Description | Expected Result | Pass/Fail |
|------|-------------|-----------------|-----------|
| `test_deletes_interview_and_returns_success` | POST `/delete-interview/<id>/` | Interview deleted; returns `{"success": true}` | ✅ Pass |
| `test_get_returns_400` | GET request | Returns 400 | ✅ Pass |
| `test_requires_login` | POST while logged out | Redirects to login | ✅ Pass |
| `test_other_users_interview_returns_404` | Interview belongs to another user | Returns 404 | ✅ Pass |

#### `SaveContactTests`

| Test | Description | Expected Result | Pass/Fail |
|------|-------------|-----------------|-----------|
| `test_creates_contact_and_returns_data` | Valid JSON body | Contact created; data returned | ✅ Pass |
| `test_missing_first_name_returns_400` | No `first_name` field | Returns 400 | ✅ Pass |
| `test_get_returns_400` | GET request | Returns 400 | ✅ Pass |
| `test_requires_login` | POST while logged out | Redirects to login | ✅ Pass |

#### `UpdateContactTests`

| Test | Description | Expected Result | Pass/Fail |
|------|-------------|-----------------|-----------|
| `test_updates_contact_fields` | Updated fields in JSON body | Contact fields saved | ✅ Pass |
| `test_get_returns_400` | GET request | Returns 400 | ✅ Pass |
| `test_requires_login` | POST while logged out | Redirects to login | ✅ Pass |
| `test_other_users_contact_returns_404` | Contact belongs to another user | Returns 404 | ✅ Pass |

#### `DeleteContactTests`

| Test | Description | Expected Result | Pass/Fail |
|------|-------------|-----------------|-----------|
| `test_deletes_contact_and_returns_success` | POST `/contacts/<id>/delete/` | Contact deleted; returns `{"success": true}` | ✅ Pass |
| `test_get_returns_400` | GET request | Returns 400 | ✅ Pass |
| `test_requires_login` | POST while logged out | Redirects to login | ✅ Pass |
| `test_other_users_contact_returns_404` | Contact belongs to another user | Returns 404 | ✅ Pass |

#### `CompanyCreateViewTests`

| Test | Description | Expected Result | Pass/Fail |
|------|-------------|-----------------|-----------|
| `test_creates_company_and_redirects` | Valid form POST | Company created; redirects to company list | ✅ Pass |
| `test_missing_name_rerenders_form` | `name` left blank | Re-renders form with errors | ✅ Pass |
| `test_requires_login` | POST while logged out | Redirects to login | ✅ Pass |

#### `CompanyUpdateViewTests`

| Test | Description | Expected Result | Pass/Fail |
|------|-------------|-----------------|-----------|
| `test_updates_company_and_redirects` | Valid form POST | Company updated; redirects to company list | ✅ Pass |
| `test_other_users_company_returns_404` | Company belongs to another user | Returns 404 | ✅ Pass |
| `test_requires_login` | POST while logged out | Redirects to login | ✅ Pass |

#### `CompanyDeleteViewTests`

| Test | Description | Expected Result | Pass/Fail |
|------|-------------|-----------------|-----------|
| `test_deletes_company_and_redirects` | POST to delete confirmation | Company deleted; redirects to company list | ✅ Pass |
| `test_other_users_company_returns_404` | Company belongs to another user | Returns 404 | ✅ Pass |
| `test_requires_login` | POST while logged out | Redirects to login | ✅ Pass |

---

### Stripe Payment Tests

**File:** `tracker/test_views.py`

Stripe API calls are mocked with `unittest.mock.patch` so no real network requests are made. The webhook handler is tested by mocking `stripe.Webhook.construct_event` to return a controlled event payload.

#### `PaymentSuccessViewTests`

| Test | Description | Expected Result | Pass/Fail |
|------|-------------|-----------------|-----------|
| `test_renders_payment_success_page` | GET `/payment-success/` | Returns 200 with `payment_success.html` | ✅ Pass |
| `test_accessible_without_login` | GET while logged out | Returns 200 (public page) | ✅ Pass |

#### `PaymentCancelViewTests`

| Test | Description | Expected Result | Pass/Fail |
|------|-------------|-----------------|-----------|
| `test_renders_payment_cancel_page` | GET `/payment-cancel/` | Returns 200 with `payment_cancel.html` | ✅ Pass |
| `test_accessible_without_login` | GET while logged out | Returns 200 (public page) | ✅ Pass |

#### `CreateCheckoutSessionTests`

| Test | Description | Expected Result | Pass/Fail |
|------|-------------|-----------------|-----------|
| `test_redirects_to_stripe_checkout_url` | GET `/subscribe/` (Stripe mocked) | Redirects to the URL returned by Stripe | ✅ Pass |
| `test_session_includes_user_id_as_client_reference` | GET `/subscribe/` | `client_reference_id` equals the logged-in user's ID | ✅ Pass |
| `test_session_includes_user_email` | GET `/subscribe/` | `customer_email` equals the user's email address | ✅ Pass |
| `test_session_uses_subscription_mode` | GET `/subscribe/` | `mode` is `"subscription"` | ✅ Pass |
| `test_requires_login` | GET `/subscribe/` while logged out | Redirects to login | ✅ Pass |

#### `StripeWebhookTests`

| Test | Description | Expected Result | Pass/Fail |
|------|-------------|-----------------|-----------|
| `test_checkout_completed_grants_premium` | `checkout.session.completed` event for a known user | `profile.is_premium` set to `True`; returns 200 | ✅ Pass |
| `test_checkout_completed_saves_stripe_customer_id` | `checkout.session.completed` event with customer ID | `profile.stripe_customer_id` saved | ✅ Pass |
| `test_checkout_completed_unknown_user_returns_200` | `checkout.session.completed` with an unknown user ID | Returns 200 silently (no crash) | ✅ Pass |
| `test_unhandled_event_type_returns_200_without_granting_premium` | Unhandled event type | Returns 200; `is_premium` remains `False` | ✅ Pass |
| `test_webhook_accessible_without_login` | POST to webhook while logged out | Returns 200 (webhooks are unauthenticated by design) | ✅ Pass |

---

## Manual Testing

### Authentication

| Test | Steps | Expected Result | Pass/Fail |
|------|-------|-----------------|-----------|
| User registration | Navigate to `/accounts/register/`, fill in all fields, submit | Account created, redirected to home | ✅ Pass |
| Register with duplicate username | Submit registration with an existing username | Error message displayed | ✅ Pass |
| Register with mismatched passwords | Submit with `password1 ≠ password2` | Error message displayed | ✅ Pass |
| Login with valid credentials | Navigate to `/accounts/login/`, enter correct details | Redirected to home page | ✅ Pass |
| Login with wrong password | Enter incorrect password | Error message displayed | ✅ Pass |
| Access protected page without login | Navigate to `/home/` while logged out | Redirected to login page | ✅ Pass |
| Logout | Click the logout button in the sidebar | Session ended, redirected to login | ✅ Pass |

---

### Job Tracker Board

| Test | Steps | Expected Result | Pass/Fail |
|------|-------|-----------------|-----------|
| Add application | Click `+ Add Application`, fill in required fields, submit | Card appears in the correct status column | ✅ Pass |
| Add application with missing required field | Submit form with `job_title` blank | Error shown, application not created | ✅ Pass |
| Add application with invalid website URL | Enter `not-a-url` in the website field | Error shown | ✅ Pass |
| Drag card to new column | Drag an application card to a different status column | Card moves; status updated in database | ✅ Pass |
| Edit application | Click edit on a card, change job title, save | Updated job title displayed on card | ✅ Pass |
| Delete application | Click delete on a card, confirm | Card removed from board | ✅ Pass |
| Applications data isolation | Log in as a second user | First user's applications are not visible | ✅ Pass |

---

### Interview Management

| Test | Steps | Expected Result | Pass/Fail |
|------|-------|-----------------|-----------|
| Add interview round | Open application card, click `Add Interview`, fill in details | Interview appears under the application | ✅ Pass |
| Add interview with no date | Submit interview form with date blank | Error shown | ✅ Pass |
| Edit interview round | Click edit on an interview, change notes, save | Updated notes displayed | ✅ Pass |
| Delete interview round | Click delete on an interview | Interview removed | ✅ Pass |
| Empty state | View Interviews page with no interviewing applications | "No active interviews" message displayed | ✅ Pass |
| Interviews page | Move application to Interviewing, visit `/interviews/` | Application and its rounds appear on the page | ✅ Pass |

---

### Company Management

| Test | Steps | Expected Result | Pass/Fail |
|------|-------|-----------------|-----------|
| Add company | Navigate to `/companies/add/`, submit valid form | Company appears in company list | ✅ Pass |
| Edit company | Click edit on a company, change name, save | Updated name displayed | ✅ Pass |
| Delete company | Click delete on a company, confirm | Company removed from list | ✅ Pass |
| Company isolation | Log in as second user | Only own companies visible | ✅ Pass |

---

### Contacts Directory

| Test | Steps | Expected Result | Pass/Fail |
|------|-------|-----------------|-----------|
| Add contact | Open Contacts, click `Add Contact`, submit | Contact appears in the directory | ✅ Pass |
| Add contact with no first name | Submit with `first_name` blank | Error shown | ✅ Pass |
| Edit contact | Click edit on a contact, update email, save | Updated email displayed | ✅ Pass |
| Delete contact | Click delete on a contact, confirm | Contact removed | ✅ Pass |
| Contact isolation | Log in as second user | Only own contacts visible | ✅ Pass |

---

### Analytics Page

| Test | Steps | Expected Result | Pass/Fail |
|------|-------|-----------------|-----------|
| Empty state | Visit `/analytics/` with no applications | "No data yet" message and prompt to go to tracker | ✅ Pass |
| Stat cards | Add several applications across statuses | Total, this week, this month, and interview rate cards show correct values | ✅ Pass |
| Monthly bar chart | Add applications with varying `date_applied` dates | Bar chart reflects correct monthly counts | ✅ Pass |
| Status donut chart | Add applications with different statuses | Donut chart slices match the status breakdown | ✅ Pass |
| Application funnel | Add applications, move some to interviewing and offer | Funnel bars show correct proportions | ✅ Pass |
| Conversion metrics | Add applications, record interviews | Response rate, offer rate, total interview rounds all correct | ✅ Pass |

---

### Help & Support Page

| Test | Steps | Expected Result | Pass/Fail |
|------|-------|-----------------|-----------|
| Page loads | Click `Help & Support` in the sidebar | Page renders correctly | ✅ Pass |
| Getting Started steps | View the page | 4 numbered steps visible with icons | ✅ Pass |
| FAQ accordion | Click on a question | Answer expands; other answers stay collapsed | ✅ Pass |
| Contact support link | Click the support email link | Email client opens with the support address pre-filled | ✅ Pass |
| Sidebar active state | Visit `/help/` | Help & Support item is highlighted in the sidebar | ✅ Pass |

---

### Subscription & Payments

| Test | Steps | Expected Result | Pass/Fail |
|------|-------|-----------------|-----------|
| Access subscribe page | Click `Upgrade` in the sidebar | Redirected to Stripe Checkout | ✅ Pass |
| Complete payment (test card) | Use Stripe test card `4242 4242 4242 4242` | Redirected to payment success page; account shows Premium | ✅ Pass |
| Cancel payment | Click Cancel on Stripe Checkout | Redirected to payment cancel page; no charge made | ✅ Pass |
| Premium badge in sidebar | Log in with premium account | Sidebar footer shows "Premium" | ✅ Pass |
| Free plan label | Log in with free account | Sidebar footer shows "Free Plan" | ✅ Pass |
| Unauthenticated access to subscribe | Visit `/subscribe/` while logged out | Redirected to login page | ✅ Pass |

---

## Validation

### Lighthouse

Lighthouse audits were run against the deployed landing page. The following issues were identified and resolved.

![lighthouse initial report ](static/images/lighthouse-initial-report.png)

---

#### Performance

##### 1. Render-Blocking Requests — Est. savings: 340 ms

All four CSS resources (Bootstrap, Bootstrap Icons, `base.css`, `style-landing.css`) were loaded with blocking `<link rel="stylesheet">` tags, preventing the browser from rendering until all had downloaded.

**Fix:** Converted every stylesheet to a non-blocking preload pattern:
```html
<link rel="preload" href="..." as="style" onload="this.onload=null;this.rel='stylesheet'">
<noscript><link rel="stylesheet" href="..."></noscript>
```
Added inline critical CSS (`body`, `.navbar`, `.hero-section`) to prevent a flash of unstyled content (FOUC) while the deferred sheets load. Also removed the `@import url('base.css')` from `style-landing.css` (sequential blocking fetch) and linked `base.css` directly as a parallel `<link>` tag instead.

---

##### 2. LCP Request Discovery — Est. savings: varies

The Largest Contentful Paint (LCP) element (the hero image) was not being prioritised by the browser, meaning it could be delayed behind lower-priority resources.

**Fix:** Added `fetchpriority="high"` to the hero `<img>` tag so the browser fetches it immediately on navigation.

---

##### 3. Network Dependency Chain — Max critical path latency: 233 ms

Two chained requests were extending the critical path: `bootstrap-icons.css` had to be fully parsed before the browser discovered and downloaded the `.woff2` font file.

**Fix:** Three additions to `<head>` in `landing.html`:
- `rel="preconnect"` to `cdn.jsdelivr.net` — establishes the TCP/TLS connection early, saving ~80 ms
- `rel="dns-prefetch"` as a fallback for older browsers
- `rel="preload"` for the Bootstrap Icons `.woff2` font — breaks the CSS→font chain so the font downloads in parallel with the CSS

---

##### 4. Improve Image Delivery — Est. savings: 146 KiB

Both Unsplash images were requested at `w=1080` but displayed at approximately 636 px wide, downloading ~145 KiB more data than necessary.

**Fix:** Updated both `<img>` tags with:
- `src` reduced to `w=640` (the approximate display width)
- `srcset` serving `640w` for standard screens and `1280w` for retina/2x displays
- `sizes="(max-width: 991px) 100vw, 50vw"` so the browser selects the correct variant before downloading

---

##### 5. Document Request Latency — Est. savings: 14 KiB

Django was not compressing HTML responses, meaning the HTML document was served uncompressed.

**Fix:** Added `django.middleware.gzip.GZipMiddleware` as the first entry in `MIDDLEWARE` in `settings.py`. It must be first so it wraps all subsequent middleware responses. WhiteNoise already handles compression for static files (CSS/JS); this covers the remaining HTML document.

---

##### 6. Font Display — Est. savings: 20 ms

The Bootstrap Icons CDN CSS does not include `font-display: swap`, causing the browser to block text rendering while the font file loads.

**Fix:** Added a `@font-face` override at the top of `base.css` using the same family name and font file URLs as the CDN. The browser deduplicates the declarations and applies `font-display: swap` from our rule, so icons render immediately with a fallback font and swap in once the `.woff2` has loaded.

---

##### 7. Image Elements Without Explicit Width and Height

Without `width` and `height` attributes, the browser cannot reserve space for images before they load, causing layout shifts (CLS).

**Fix:** Added explicit dimensions matching each image's intrinsic aspect ratio:

| Image | Dimensions | Aspect ratio |
|-------|-----------|--------------|
| Hero (portrait) | `width="640" height="960"` | 2:3 |
| Benefits (landscape) | `width="640" height="360"` | 16:9 |

`img-fluid` (`max-width: 100%; height: auto`) keeps them fully responsive; the attributes simply inform the browser of the ratio for layout reservation.

---

#### Accessibility

##### 1. Insufficient Colour Contrast

Several elements failed the WCAG AA minimum contrast ratio of 4.5:1 for normal text.

**Fix:**

| Element | Before | After | Contrast ratio |
|---------|--------|-------|----------------|
| `.btn-primary` background | `#0d9488` | `#0f766e` | 3.7:1 → 5.2:1 ✅ |
| `.badge-custom` text | `#0d9488` on `#f0fdfa` | `#0f766e` on `#f0fdfa` | 3.6:1 → 5.0:1 ✅ |
| `.btn-outline-secondary` text | `#6c757d` | `#343a40` | 4.4:1 → 10.5:1 ✅ |
| `.cta-section .text-muted` | `#6c757d` | `#555e68` | 4.2:1 → 5.5:1 ✅ |

The button colours remain visually teal; only the shade was darkened slightly.

---

##### 2. Links Without a Discernible Name

The four social icon links in the footer contained only a `<i>` icon element with no visible or accessible label, making them unreadable by screen readers.

**Fix:** Added `aria-label` to each `<a>` (e.g. `aria-label="Follow us on Twitter"`) and `aria-hidden="true"` to each `<i>` to prevent the icon glyph name from being announced redundantly.

---

##### 3. Heading Elements Not in Sequentially-Descending Order

Section headings jumped from `h2` directly to `h5` (feature cards, steps, benefits) and `h6` (footer columns), skipping levels and breaking the document outline for screen readers.

**Fix:** Changed all sub-section headings to `h3`. Bootstrap's `fs-5` and `fs-6` utility classes were added to preserve the original visual size:

```
h1  Land Your Dream Job Faster
  h2  Stay Organised on your job hunt
    h3  Centralized Dashboard, Smart Reminders, …  (was h5)
  h2  How Trackwise Works
    h3  Create Your Account, Add Applications, …   (was h5)
  h2  Why Job Seekers Love Trackwise
    h3  Save 5+ Hours Per Week, …                  (was h5)
  h2  Ready to Transform Your Job Search?
  h3  Product / Resources / Company                (was h6, footer nav)
```

---

##### 4. Document Does Not Have a Main Landmark

The page had no `<main>` element, so assistive technologies could not offer a "skip to main content" navigation shortcut.

**Fix:** Wrapped all content between `<nav>` and `<footer>` in a `<main>` element.



Lighthouse Report after all the fixes had been applied:


![lighthouse report after fixes ](static/images/after-fixes-report.png)






### W3C HTML validator

HTML validated using the [W3C Markup Validation Service](https://validator.w3.org/).

| Page | Result |
|------|--------|
| Landing page | Document checking completed. No errors or warnings to show. |
| Login page | Document checking completed. No errors or warnings to show. |
| Register page | Document checking completed. No errors or warnings to show. |
| Home page | Document checking completed. No errors or warnings to show |
| Tracker board | Document checking completed. No errors or warnings to show. |
| Interviews page | Document checking completed. No errors or warnings to show. |
| Contacts page | Document checking completed. No errors or warnings to show. |
| Analytics page | Document checking completed. No errors or warnings to show |
| Help & Support page | Document checking completed. No errors or warnings to show. |
| Payment success page | Document checking completed. No errors or warnings to show. |
| Payment cancel page | Document checking completed. No errors or warnings to show. |

### CSS Validation

CSS validated using the [W3C CSS Validation Service](https://jigsaw.w3.org/css-validator/).

| File | Result |
|------|--------|
| `static/css/base.css` | No Error Found |
| `static/css/style.css` | No Error Found |
| `static/css/style-auth.css` | No errors |
| `static/css/style-landing.css` | No Error Found |
| `static/css/style-tracker.css` | No Error Found |
| `static/css/style-interviews.css` | No Error Found |
| `static/css/style-analytics.css` | No Error Found |
| `static/css/style-help.css` | No Error Found |
| `static/css/payment.css` | No Error Found |

### JavaScript Validation

JavaScript validated using [JSHint](https://jshint.com/).

| File | Result |
|------|--------|
| `static/js/script-home.js` | No errors |
| `static/js/tracker.js` | No errors |

### Python Linting

Python code checked using `flake8`.

```bash
flake8 tracker/ accounts/ jobtracker/ --max-line-length=120
```

| Module | Result |
|--------|--------|
| `tracker/` | No errors |
| `accounts/` | No errors |
| `jobtracker/` | No errors |

---

## Browser Compatibility

Tested on the following browsers:

| Browser | Version | Result |
|---------|---------|--------|
| Google Chrome | Latest | ✅ Pass |
| Mozilla Firefox | Latest | ✅ Pass |
| Microsoft Edge | Latest | ✅ Pass |
| Safari (macOS) | Latest | ✅ Pass |

---

## Responsiveness Testing

Tested using Chrome DevTools device emulation and on physical devices.

| Device / Breakpoint | Layout | Tracker Board | Notes |
|--------------------|--------|---------------|-------|
| iPhone SE (375px) | ✅ | Horizontal scroll with snap | Columns fill ~90% of viewport |
| iPhone 14 (390px) | ✅ | Horizontal scroll with snap | |
| iPad (768px) | ✅ | Fixed 300px columns | |
| iPad Pro (1024px) | ✅ | Full-width flex columns | |
| Desktop (1280px+) | ✅ | Full-width flex columns | |

---

## Known Issues

| Issue | Status |
|-------|--------|
| Documents and Settings sidebar items are placeholders with no linked pages | Not yet implemented |
| Stripe subscription cancellation requires emailing support (no self-service portal) | By design for current version |
