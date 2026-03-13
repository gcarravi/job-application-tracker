from django.urls import path
from . import views
from .views import LandingView, HomeView
from .views import TrackerBoardView, InterviewsView, ContactsView
from .views import (
    CompanyListView,
    CompanyCreateView,
    CompanyUpdateView,
    CompanyDeleteView,
)

urlpatterns = [
    path('', LandingView.as_view(), name='landing'),
    path('home/', HomeView.as_view(), name='home'),
    path("tracker/", TrackerBoardView.as_view(), name="tracker"),
    path("interviews/", InterviewsView.as_view(), name="interviews"),
    path("companies/", CompanyListView.as_view(), name="company_list"),
    path("companies/add/", CompanyCreateView.as_view(), name="company_add"),
    path("companies/<int:pk>/edit/", CompanyUpdateView.as_view(), name="company_edit"),
    path("companies/<int:pk>/delete/", CompanyDeleteView.as_view(), name="company_delete"),
    path('update-job-status/<int:job_id>/', views.update_job_status, name='update-job-status'),
    path('delete-job/<int:job_id>/', views.delete_job, name='delete_job'),
    path("get-job/<int:job_id>/", views.get_job, name="get_job"),
    path("update-job/<int:job_id>/", views.update_job, name="update_job"),
    path("get-interviews/<int:app_id>/", views.get_interviews, name="get_interviews"),
    path("save-interview/<int:app_id>/", views.save_interview, name="save_interview"),
    path("update-interview/<int:interview_id>/", views.update_interview, name="update_interview"),
    path("delete-interview/<int:interview_id>/", views.delete_interview, name="delete_interview"),
    path("contacts/", ContactsView.as_view(), name="contacts"),
    path("contacts/api/", views.get_contacts_api, name="get_contacts_api"),
    path("contacts/save/", views.save_contact, name="save_contact"),
    path("contacts/<int:contact_id>/update/", views.update_contact, name="update_contact"),
    path("contacts/<int:contact_id>/delete/", views.delete_contact, name="delete_contact"),
    path('subscribe/', views.create_checkout_session, name="subscribe"),
    path("stripe/webhook/", views.stripe_webhook),
    path("payment-success/", views.payment_success, name="payment_success"),
    path("payment-cancel/", views.payment_cancel, name="payment_cancel"),
]