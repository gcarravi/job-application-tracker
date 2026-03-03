from django.shortcuts import render
from django.contrib.auth.decorators import login_required
# from django.http import HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views.generic import TemplateView
from django.views.generic import ListView
from django.views.generic import CreateView
from django.views.generic import UpdateView
from django.views.generic import DeleteView
from django.urls import reverse_lazy
from .models import Company, Application
from .forms import ApplicationForm

# Create your views here.
# def app_tracker(request):
#     return HttpResponse("Hello, Job Application Tracker - from TRACKER app")


@login_required
def dashboard(request):
    return render(request, 'tracker/dashboard.html')


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "tracker/dashboard.html"    


class HomeView(TemplateView):
    template_name = "home.html"


class TrackerBoardView(LoginRequiredMixin, TemplateView):
    template_name = "tracker/tracker.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        context["wishlist"] = Application.objects.filter(user=user, status="wishlist")
        context["applied"] = Application.objects.filter(user=user, status="applied")
        context["interviewing"] = Application.objects.filter(user=user, status="interviewing")
        context["offer"] = Application.objects.filter(user=user, status="offer")
        context["rejected"] = Application.objects.filter(user=user, status="rejected")
        context["ghosted"] = Application.objects.filter(user=user, status="ghosted")
        context["follow_up"] = Application.objects.filter(user=user, status="follow_up")

        context["form"] = ApplicationForm(user=self.request.user)

        return context
    

    def post(self, request, *args, **kwargs):
        form = ApplicationForm(request.POST, user=request.user)

        if form.is_valid():
            application = form.save(commit=False)
            application.user = request.user
            application.save()
            return redirect("tracker_board")

        # If form invalid, re-render page with errors
        context = self.get_context_data()
        context["form"] = form
        return self.render_to_response(context)


class CompanyListView(LoginRequiredMixin, ListView):
    model = Company
    template_name = "tracker/company_list.html"
    context_object_name = "companies"

    def get_queryset(self):
        return Company.objects.filter(user=self.request.user)
    

class CompanyCreateView(LoginRequiredMixin, CreateView):
    model = Company
    fields = ["name", "website", "location"]
    template_name = "tracker/company_form.html"
    success_url = reverse_lazy("company_list")

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)
    

class CompanyUpdateView(LoginRequiredMixin, UpdateView):
    model = Company
    fields = ["name", "website", "location"]
    template_name = "tracker/company_form.html"
    success_url = reverse_lazy("company_list")

    def get_queryset(self):
        return Company.objects.filter(user=self.request.user)
    

class CompanyDeleteView(LoginRequiredMixin, DeleteView):
    model = Company
    template_name = "tracker/company_confirm_delete.html"
    success_url = reverse_lazy("company_list")

    def get_queryset(self):
        return Company.objects.filter(user=self.request.user)    
