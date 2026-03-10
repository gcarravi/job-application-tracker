from django.urls import path
from . import views
# from .views import DashboardView, HomeView
from .views import DashboardView, LandingView, HomeView
from .views import TrackerBoardView
from .views import (
    CompanyListView,
    CompanyCreateView,
    CompanyUpdateView,
    CompanyDeleteView,
)

urlpatterns = [
    path('', LandingView.as_view(), name='landing'),
    path('home/', HomeView.as_view(), name='home'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path("tracker/", TrackerBoardView.as_view(), name="tracker"),
    path("companies/", CompanyListView.as_view(), name="company_list"),
    path("companies/add/", CompanyCreateView.as_view(), name="company_add"),
    path("companies/<int:pk>/edit/", CompanyUpdateView.as_view(), name="company_edit"),
    path("companies/<int:pk>/delete/", CompanyDeleteView.as_view(), name="company_delete"),
    path('update-job-status/<int:job_id>/', views.update_job_status, name='update-job-status'),
    path('delete-job/<int:job_id>/', views.delete_job, name='delete_job'),
    path("get-job/<int:job_id>/", views.get_job, name="get_job"),
    path("update-job/<int:job_id>/", views.update_job, name="update_job"),
    path('subscribe/', views.create_checkout_session, name="subscribe"),
    path("stripe/webhook/", views.stripe_webhook),
    path("payment-success/", views.payment_success, name="payment_success"),
    path("payment-cancel/", views.payment_cancel, name="payment_cancel"),
]