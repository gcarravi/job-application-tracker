from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

# Create your views here.
def app_tracker(request):
    return HttpResponse("Hello, Job Application Tracker - from TRACKER app")


@login_required
def dashboard(request):
    return render(request, 'tracker/dashboard.html')
