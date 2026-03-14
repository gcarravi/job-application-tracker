# Trackwise – Testing Documentation

This document covers all testing carried out on the Trackwise application, including automated tests, manual functional testing, and validation.

---

## Table of Contents

- [Running the Automated Tests](#running-the-automated-tests)
- [Automated Tests](#automated-tests)
  - [ApplicationForm Tests](#applicationform-tests)
  - [RegisterForm Tests](#registerform-tests)
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

**Current result:** 37 tests, 0 failures, 0 errors.

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

### HTML Validation

HTML validated using the [W3C Markup Validation Service](https://validator.w3.org/).

| Page | Result |
|------|--------|
| Landing page | No errors |
| Login page | No errors |
| Register page | No errors |
| Home / Dashboard | No errors |
| Tracker board | No errors |
| Interviews page | No errors |
| Contacts page | No errors |
| Analytics page | No errors |
| Help & Support page | No errors |
| Payment success page | No errors |
| Payment cancel page | No errors |

### CSS Validation

CSS validated using the [W3C CSS Validation Service](https://jigsaw.w3.org/css-validator/).

| File | Result |
|------|--------|
| `static/css/base.css` | No errors |
| `static/css/style.css` | No errors |
| `static/css/style-auth.css` | No errors |
| `static/css/style-landing.css` | No errors |
| `static/css/style-tracker.css` | No errors |
| `static/css/payment.css` | No errors |

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
