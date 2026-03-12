from django.contrib import admin
from .models import Company, Application, Interview, Contact, Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_premium', 'stripe_customer_id')
    list_filter = ('is_premium',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name')


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'website', 'user', 'created_at')
    search_fields = ('name', 'location')
    list_filter = ('user',)


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'job_title', 'email', 'phone', 'user', 'created_at')
    search_fields = ('first_name', 'last_name', 'email', 'job_title')
    list_filter = ('user',)


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('job_title', 'company', 'status', 'date_applied', 'recruiter', 'user')
    search_fields = ('job_title', 'company__name')
    list_filter = ('status', 'user')
    date_hierarchy = 'date_applied'


@admin.register(Interview)
class InterviewAdmin(admin.ModelAdmin):
    list_display = ('interview_type', 'application', 'date', 'result')
    search_fields = ('application__job_title', 'application__company__name')
    list_filter = ('interview_type', 'result')
    date_hierarchy = 'date'
