from django.contrib.auth.decorators import login_required
from django.db.models import Subquery, OuterRef, Count
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.http import JsonResponse, HttpResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json
from datetime import datetime, date, timedelta
import calendar as _cal
from .models import Company, Application, Interview, Contact, Document
from .forms import ApplicationForm
import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY

# Mixin that injects user_initials and full_name into every view that uses base.html
class UserContextMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["full_name"] = f"{user.first_name} {user.last_name}".strip() or user.username
        context["user_initials"] = (user.first_name[:1] + user.last_name[:1]).upper() or user.username[:2].upper()
        return context


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

        user_id = session.get('client_reference_id')
        stripe_customer_id = session.get('customer')

        user = User.objects.filter(id=user_id).first()
        if user:
            user.profile.is_premium = True
            if stripe_customer_id:
                user.profile.stripe_customer_id = stripe_customer_id
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
        "document_ids": list(job.documents.values_list('id', flat=True)),
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


@login_required
def create_checkout_session(request):

    checkout_session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        mode='subscription',
        customer_email=request.user.email,
        client_reference_id=str(request.user.id),
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


class DocumentsView(UserContextMixin, LoginRequiredMixin, TemplateView):
    template_name = "tracker/documents.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["documents"] = Document.objects.filter(user=self.request.user).order_by('-created_at')
        return context


@login_required
@csrf_exempt
def upload_document(request):
    if request.method == 'POST' and request.FILES.get('file'):
        name = request.POST.get('name', '').strip()
        file_type = request.POST.get('file_type', 'cv')
        if not name:
            return JsonResponse({'success': False, 'error': 'Name is required'}, status=400)
        doc = Document.objects.create(
            user=request.user,
            name=name,
            file=request.FILES['file'],
            file_type=file_type,
        )
        return JsonResponse({
            'success': True,
            'id': doc.id,
            'name': doc.name,
            'file_type': doc.get_file_type_display(),
            'url': doc.file.url,
            'created_at': doc.created_at.strftime('%d %b %Y'),
        })
    return JsonResponse({'success': False, 'error': 'No file provided'}, status=400)


@login_required
@csrf_exempt
def delete_document(request, doc_id):
    if request.method == 'POST':
        doc = get_object_or_404(Document, id=doc_id, user=request.user)
        doc.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)


@login_required
def get_documents_api(request):
    docs = Document.objects.filter(user=request.user).order_by('-created_at')
    data = [{'id': d.id, 'name': d.name, 'file_type': d.get_file_type_display(), 'url': d.file.url} for d in docs]
    return JsonResponse({'documents': data})


@login_required
@csrf_exempt
def update_job_documents(request, job_id):
    if request.method == 'POST':
        application = get_object_or_404(Application, id=job_id, user=request.user)
        data = json.loads(request.body)
        doc_ids = data.get('document_ids', [])
        application.documents.set(Document.objects.filter(id__in=doc_ids, user=request.user))
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)


class LandingView(TemplateView):
    template_name = "landing.html"


class HomeView(UserContextMixin, LoginRequiredMixin, TemplateView):
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
        context["total_applications"] = Application.objects.filter(user=user).count()
        context["total_interviews"] = Application.objects.filter(user=user, status="interviewing").count()
        context["total_in_review"] = Application.objects.filter(user=user, status="applied").count()
        context["total_offers"] = Application.objects.filter(user=user, status="offer").count()
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

        # ── Notifications ──────────────────────────────────────────────────
        today = timezone.now().date()

        # 1. Interviews in the next 3 days
        soon_interviews = (
            Interview.objects
            .filter(
                application__user=user,
                date__gte=timezone.now(),
                date__lte=timezone.now() + timedelta(days=3),
            )
            .select_related("application", "application__company")
            .order_by("date")
        )

        # 2. Applications stale in "applied" for 5+ days
        stale_apps = (
            Application.objects
            .filter(user=user, status="applied", date_applied__lte=today - timedelta(days=5))
            .select_related("company")
            .order_by("date_applied")[:5]
        )

        # 3. Wishlist items not acted on for 14+ days
        wishlist_apps = (
            Application.objects
            .filter(user=user, status="wishlist", date_applied__lte=today - timedelta(days=14))
            .select_related("company")
            .order_by("date_applied")[:5]
        )

        # 4. Pending offers
        offer_apps = (
            Application.objects
            .filter(user=user, status="offer")
            .select_related("company")[:3]
        )

        notifications = []

        for iv in soon_interviews:
            days_until = (iv.date.date() - today).days
            if days_until == 0:
                when = "today"
            elif days_until == 1:
                when = "tomorrow"
            else:
                when = f"in {days_until} days"
            notifications.append({
                'icon': 'fa-calendar-check',
                'color': 'teal',
                'title': iv.application.company.name,
                'text': f'{iv.interview_type} {when} · {iv.date.strftime("%d %b, %H:%M")}',
                'urgency': 'high' if days_until <= 1 else 'medium',
            })

        for app in stale_apps:
            days_stale = (today - app.date_applied).days
            notifications.append({
                'icon': 'fa-clock',
                'color': 'blue',
                'title': app.company.name,
                'text': f'Applied {days_stale} days ago — consider sending a follow-up',
                'urgency': 'medium',
            })

        for app in wishlist_apps:
            days_old = (today - app.date_applied).days
            notifications.append({
                'icon': 'fa-bookmark',
                'color': 'purple',
                'title': app.company.name,
                'text': f'Wishlisted {days_old} days ago — ready to apply?',
                'urgency': 'low',
            })

        for app in offer_apps:
            notifications.append({
                'icon': 'fa-trophy',
                'color': 'green',
                'title': app.company.name,
                'text': f'Offer for {app.job_title} — don\'t leave them waiting!',
                'urgency': 'high',
            })

        context['notifications'] = notifications
        context['total_notifications'] = len(notifications)
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



class TrackerBoardView(UserContextMixin, LoginRequiredMixin, TemplateView):
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


class HelpView(UserContextMixin, LoginRequiredMixin, TemplateView):
    template_name = "tracker/help.html"


class InterviewsView(UserContextMixin, LoginRequiredMixin, TemplateView):
    template_name = "tracker/interviews.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["applications"] = (
            Application.objects
            .filter(user=user, status="interviewing")
            .select_related("company")
            .prefetch_related("interviews", "interviews__interviewers")
            .order_by("-created_at")
        )
        context["total_rounds"] = Interview.objects.filter(
            application__user=user, application__status="interviewing"
        ).count()
        return context


class ContactsView(UserContextMixin, LoginRequiredMixin, TemplateView):
    template_name = "tracker/contacts.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["contacts"] = Contact.objects.filter(user=user).order_by('first_name', 'last_name')
        return context


class AnalyticsView(UserContextMixin, LoginRequiredMixin, TemplateView):
    template_name = "tracker/analytics.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        now = timezone.now()
        today = now.date()

        apps = Application.objects.filter(user=user)
        total = apps.count()

        # Stat cards
        this_week = apps.filter(created_at__gte=now - timedelta(days=7)).count()
        this_month = apps.filter(created_at__gte=now - timedelta(days=30)).count()
        interviewing_count = apps.filter(status='interviewing').count()
        offer_count = apps.filter(status='offer').count()
        conversion = round((interviewing_count + offer_count) / total * 100) if total > 0 else 0

        # Conversion metrics
        responded = apps.filter(status__in=['interviewing', 'offer', 'rejected', 'ghosted']).count()
        response_rate = round(responded / total * 100) if total > 0 else 0
        offer_rate = round(offer_count / total * 100) if total > 0 else 0
        total_interviews = Interview.objects.filter(application__user=user).count()

        # Status breakdown (donut chart)
        status_data = dict(
            apps.values_list('status').annotate(c=Count('id')).values_list('status', 'c')
        )
        status_order = ['wishlist', 'applied', 'interviewing', 'offer', 'rejected', 'ghosted', 'follow_up']
        status_labels = ['Wishlist', 'Applied', 'Interviewing', 'Offer', 'Rejected', 'Ghosted', 'Follow Up']
        status_colors = ['#94a3b8', '#3b82f6', '#0d9488', '#22c55e', '#ef4444', '#9ca3af', '#f59e0b']
        status_counts_list = [status_data.get(s, 0) for s in status_order]

        # Monthly applications — last 6 months (by date_applied)
        monthly_labels = []
        monthly_counts = []
        for i in range(5, -1, -1):
            month = today.month - i
            year = today.year
            while month <= 0:
                month += 12
                year -= 1
            first_day = date(year, month, 1)
            last_day = date(year, month, _cal.monthrange(year, month)[1])
            count = apps.filter(date_applied__gte=first_day, date_applied__lte=last_day).count()
            monthly_labels.append(first_day.strftime('%b %Y'))
            monthly_counts.append(count)

        # Funnel
        active_total = apps.filter(
            status__in=['applied', 'interviewing', 'offer', 'rejected', 'ghosted', 'follow_up']
        ).count()
        got_interview = apps.filter(status__in=['interviewing', 'offer']).count()
        funnel_max = active_total if active_total > 0 else 1
        funnel = [
            {'label': 'Total Applied', 'count': active_total, 'pct': 100},
            {'label': 'Got Interview', 'count': got_interview,
             'pct': round(got_interview / funnel_max * 100)},
            {'label': 'Received Offer', 'count': offer_count,
             'pct': round(offer_count / funnel_max * 100)},
        ]

        context.update({
            'total': total,
            'this_week': this_week,
            'this_month': this_month,
            'conversion': conversion,
            'response_rate': response_rate,
            'offer_rate': offer_rate,
            'total_interviews': total_interviews,
            'status_labels': json.dumps(status_labels),
            'status_counts': json.dumps(status_counts_list),
            'status_colors': json.dumps(status_colors),
            'monthly_labels': json.dumps(monthly_labels),
            'monthly_counts': json.dumps(monthly_counts),
            'funnel': funnel,
            'funnel_max': funnel_max,
        })
        return context
