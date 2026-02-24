from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.
def app_tracker(request):
    return HttpResponse("Hello, Job Application Tracker - from TRACKER app")
