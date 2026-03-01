from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

# Create your views here.
def app_tracker(request):
    return HttpResponse("Hello, Job Application Tracker - from TRACKER app")


@login_required
def dashboard(request):
    return render(request, 'tracker/dashboard.html')


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "tracker/dashboard.html"    


class HomeView(TemplateView):
    template_name = "home.html"    
