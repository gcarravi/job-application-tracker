from django.urls import path
from .views import DashboardView, HomeView
from .views import (
    CompanyListView,
    CompanyCreateView,
    CompanyUpdateView,
    CompanyDeleteView,
)

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path("companies/", CompanyListView.as_view(), name="company_list"),
    path("companies/add/", CompanyCreateView.as_view(), name="company_add"),
    path("companies/<int:pk>/edit/", CompanyUpdateView.as_view(), name="company_edit"),
    path("companies/<int:pk>/delete/", CompanyDeleteView.as_view(), name="company_delete"),
]