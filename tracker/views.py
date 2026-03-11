from django.contrib.auth.decorators import login_required
from django.db.models import Subquery, OuterRef
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.http import JsonResponse, HttpResponse
import json
from datetime import datetime
from .models import Company, Application, Interview, Contact
from .forms import ApplicationForm
import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY

# Create your views here.

@login_required
def dashboard(request):
    return render(request, 'tracker/dashboard.html')


# Define allowed statuses (matches the ones in the model)
ALLOWED_STATUSES = [
    'wishlist',
    'applied',
    'interviewing',
    'offer',
    'rejected',
    'ghosted',
    'follow_up'
]


@csrf_exempt
def delete_job(request, job_id):
    if request.method == 'POST':
        job = get_object_or_404(Application, id=job_id)
        job.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)


@csrf_exempt
def update_job_status(request, job_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            new_status = data.get('status')

            # Validate status
            if new_status not in ALLOWED_STATUSES:
                return JsonResponse({'success': False, 'error': 'Invalid status'}, status=400)

            # Fetch the actual model
            job = Application.objects.get(id=job_id)
            job.status = new_status
            job.save()

            return JsonResponse({'success': True, 'new_status': new_status})
        except Application.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Job not found'}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)




@csrf_exempt
def update_job(request, job_id):
    if request.method == "POST":
        job = get_object_or_404(Application, id=job_id)
        data = json.loads(request.body)
        job.status = data.get("status", job.status)
        job.notes = data.get("notes", job.notes)
        if "job_title" in data:
            job.job_title = data["job_title"]
        if "salary_range" in data:
            job.salary_range = data["salary_range"]
        if "recruiter_id" in data:
            rid = data["recruiter_id"]
            if rid:
                try:
                    job.recruiter = Contact.objects.get(id=rid, user=job.user)
                except Contact.DoesNotExist:
                    pass
            else:
                job.recruiter = None
        job.save()
        return JsonResponse({"success": True})
    return JsonResponse({"success": False}, status=400)



@csrf_exempt
def stripe_webhook(request):

    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']

    event = stripe.Webhook.construct_event(
        payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
    )

    if event['type'] == 'checkout.session.completed':

        session = event['data']['object']

        customer_email = session['customer_details']['email']

        user = User.objects.get(email=customer_email)
        user.profile.is_premium = True
        user.profile.save()

    return HttpResponse(status=200)




def get_job(request, job_id):
    job = get_object_or_404(Application, id=job_id)

    data = {
        "id": job.id,
        "company_name": job.company.name,
        "company_location": job.company.location or "",
        "company_website": job.company.website or "",
        "job_title": job.job_title,
        "salary_range": job.salary_range or "",
        "status": job.status,
        "date_applied": job.date_applied.strftime("%Y-%m-%d") if job.date_applied else "",
        "notes": job.notes or "",
        "recruiter_id": job.recruiter_id or "",
        "recruiter_name": job.recruiter.full_name if job.recruiter else "",
    }

    return JsonResponse(data)


@login_required
def get_interviews(request, app_id):
    application = get_object_or_404(Application, id=app_id, user=request.user)
    interviews = []
    for iv in application.interviews.order_by('created_at').prefetch_related('interviewers'):
        interviews.append({
            "id": iv.id,
            "interview_type": iv.interview_type,
            "date": iv.date.strftime("%Y-%m-%dT%H:%M") if iv.date else "",
            "notes": iv.notes or "",
            "result": iv.result or "",
            "interviewer_ids": [c.id for c in iv.interviewers.all()],
        })
    return JsonResponse({"interviews": interviews})


@login_required
@csrf_exempt
def save_interview(request, app_id):
    """Always creates a new interview round."""
    if request.method == "POST":
        from django.utils import timezone
        from django.utils.dateparse import parse_datetime
        application = get_object_or_404(Application, id=app_id, user=request.user)
        data = json.loads(request.body)

        date_str = data.get("date")
        if not date_str:
            return JsonResponse({"success": False, "error": "Date is required"}, status=400)

        date_val = parse_datetime(date_str)
        if date_val and timezone.is_naive(date_val):
            date_val = timezone.make_aware(date_val)
        if not date_val:
            return JsonResponse({"success": False, "error": "Invalid date"}, status=400)

        interview = Interview.objects.create(
            application=application,
            interview_type=data.get("interview_type") or "Human Resources",
            date=date_val,
            notes=data.get("notes", ""),
            result=data.get("result", ""),
        )
        interviewer_ids = data.get("interviewer_ids", [])
        if interviewer_ids:
            interview.interviewers.set(Contact.objects.filter(id__in=interviewer_ids, user=request.user))
        return JsonResponse({"success": True, "id": interview.id})
    return JsonResponse({"success": False}, status=400)


@login_required
@csrf_exempt
def update_interview(request, interview_id):
    if request.method == "POST":
        from django.utils import timezone
        from django.utils.dateparse import parse_datetime
        interview = get_object_or_404(Interview, id=interview_id, application__user=request.user)
        data = json.loads(request.body)

        date_str = data.get("date")
        if date_str:
            date_val = parse_datetime(date_str)
            if date_val and timezone.is_naive(date_val):
                date_val = timezone.make_aware(date_val)
            if date_val:
                interview.date = date_val

        interview.interview_type = data.get("interview_type") or interview.interview_type
        interview.notes = data.get("notes", "")
        interview.result = data.get("result", "")
        interview.save()
        if "interviewer_ids" in data:
            interview.interviewers.set(Contact.objects.filter(id__in=data["interviewer_ids"], user=request.user))
        return JsonResponse({"success": True})
    return JsonResponse({"success": False}, status=400)


@login_required
@csrf_exempt
def delete_interview(request, interview_id):
    if request.method == "POST":
        interview = get_object_or_404(Interview, id=interview_id, application__user=request.user)
        interview.delete()
        return JsonResponse({"success": True})
    return JsonResponse({"success": False}, status=400)


@login_required
def get_contacts_api(request):
    contacts = Contact.objects.filter(user=request.user).order_by('first_name', 'last_name')
    data = [{"id": c.id, "name": c.full_name, "job_title": c.job_title, "email": c.email} for c in contacts]
    return JsonResponse({"contacts": data})


@login_required
@csrf_exempt
def save_contact(request):
    if request.method == "POST":
        data = json.loads(request.body)
        if not data.get("first_name"):
            return JsonResponse({"success": False, "error": "First name required"}, status=400)
        contact = Contact.objects.create(
            user=request.user,
            first_name=data.get("first_name", ""),
            last_name=data.get("last_name", ""),
            email=data.get("email", ""),
            phone=data.get("phone", ""),
            job_title=data.get("job_title", ""),
            linkedin_url=data.get("linkedin_url") or None,
            notes=data.get("notes", ""),
        )
        return JsonResponse({"success": True, "id": contact.id, "name": contact.full_name, "job_title": contact.job_title, "email": contact.email, "phone": contact.phone})
    return JsonResponse({"success": False}, status=400)


@login_required
@csrf_exempt
def update_contact(request, contact_id):
    if request.method == "POST":
        contact = get_object_or_404(Contact, id=contact_id, user=request.user)
        data = json.loads(request.body)
        contact.first_name = data.get("first_name", contact.first_name)
        contact.last_name = data.get("last_name", contact.last_name)
        contact.email = data.get("email", contact.email)
        contact.phone = data.get("phone", contact.phone)
        contact.job_title = data.get("job_title", contact.job_title)
        contact.linkedin_url = data.get("linkedin_url") or None
        contact.notes = data.get("notes", contact.notes or "")
        contact.save()
        return JsonResponse({"success": True, "name": contact.full_name, "job_title": contact.job_title, "email": contact.email, "phone": contact.phone})
    return JsonResponse({"success": False}, status=400)


@login_required
@csrf_exempt
def delete_contact(request, contact_id):
    if request.method == "POST":
        contact = get_object_or_404(Contact, id=contact_id, user=request.user)
        contact.delete()
        return JsonResponse({"success": True})
    return JsonResponse({"success": False}, status=400)


def create_checkout_session(request):

    checkout_session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        mode='subscription',
        line_items=[{
            'price': 'price_1T99hJC5ICaFnwSEAdv5gQEa',  # your Stripe price id
            'quantity': 1,
        }],
        success_url=request.build_absolute_uri('/payment-success/'),
        cancel_url=request.build_absolute_uri('/payment-cancel/'),
    )

    return redirect(checkout_session.url)


def payment_success(request):
    return render(request, "payment_success.html")



def payment_cancel(request):
    return render(request, "payment_cancel.html")


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "tracker/dashboard.html"


class LandingView(TemplateView):
    template_name = "landing.html"     


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hour = datetime.now().hour
        if hour < 12:
            greeting = "Good morning"
        elif hour < 18:
            greeting = "Good afternoon"
        else:
            greeting = "Good evening"
        user = self.request.user
        context["greeting"] = greeting
        context["display_name"] = user.first_name or user.username
        context["full_name"] = f"{user.first_name} {user.last_name}".strip() or user.username
        context["total_applications"] = Application.objects.filter(user=user).count()
        context["total_interviews"] = Application.objects.filter(user=user, status="interviewing").count()
        context["total_in_review"] = Application.objects.filter(user=user, status="applied").count()
        context["total_offers"] = Application.objects.filter(user=user, status="offer").count()
        from django.utils import timezone
        # For each application, find the ID of its highest round (latest created) future interview
        next_iv_subquery = (
            Interview.objects
            .filter(application=OuterRef('pk'), date__gte=timezone.now())
            .order_by('-created_at')
            .values('id')[:1]
        )
        next_iv_ids = (
            Application.objects
            .filter(user=user)
            .annotate(next_iv_id=Subquery(next_iv_subquery))
            .filter(next_iv_id__isnull=False)
            .values_list('next_iv_id', flat=True)
        )
        context["upcoming_interviews"] = (
            Interview.objects
            .filter(id__in=next_iv_ids)
            .select_related("application", "application__company")
            .order_by("date")[:5]
        )
        context["recent_applications"] = (
            Application.objects
            .filter(user=user)
            .select_related("company")
            .order_by("-created_at")[:5]
        )
        context["form"] = ApplicationForm(user=user)
        return context
    

    def post(self, request, *args, **kwargs):
        form = ApplicationForm(request.POST, user=request.user)

        if form.is_valid():
            application = form.save(commit=False)
            application.user = request.user
            application.save()
            return redirect("tracker")

        # If form invalid, re-render page with errors
        context = self.get_context_data()
        context["form"] = form
        return self.render_to_response(context)



class TrackerBoardView(LoginRequiredMixin, TemplateView):
    template_name = "tracker/tracker.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        context["full_name"] = f"{user.first_name} {user.last_name}".strip() or user.username

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
            return redirect("tracker")

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


class InterviewsView(LoginRequiredMixin, TemplateView):
    template_name = "tracker/interviews.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["full_name"] = f"{user.first_name} {user.last_name}".strip() or user.username
        context["applications"] = (
            Application.objects
            .filter(user=user, status="interviewing")
            .select_related("company")
            .prefetch_related("interviews")
            .order_by("-created_at")
        )
        context["total_rounds"] = Interview.objects.filter(
            application__user=user, application__status="interviewing"
        ).count()
        return context


class ContactsView(LoginRequiredMixin, TemplateView):
    template_name = "tracker/contacts.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["full_name"] = f"{user.first_name} {user.last_name}".strip() or user.username
        context["contacts"] = Contact.objects.filter(user=user).order_by('first_name', 'last_name')
        return context
