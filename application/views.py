from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.
def my_job_application(request):
    return HttpResponse("Hello, Job Application Tracker!")
