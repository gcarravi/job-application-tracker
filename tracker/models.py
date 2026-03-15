from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from cloudinary.models import CloudinaryField

# Create your models here.

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    Profile.objects.get_or_create(user=instance)


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_premium = models.BooleanField(default=False)
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
    photo = CloudinaryField('image', blank=True, null=True)

    def __str__(self):
        return self.user.username    


class Company(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='companies')
    name = models.CharField(max_length=255)
    website = models.URLField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    


class Contact(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contacts')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    job_title = models.CharField(max_length=255, blank=True)
    linkedin_url = models.URLField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}".strip() or self.first_name

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.first_name


class Application(models.Model):

    STATUS_CHOICES = [
        ('wishlist', 'Wishlist'),
        ('applied', 'Applied'),
        ('interviewing', 'Interviewing'),
        ('offer', 'Offer'),
        ('rejected', 'Rejected'),
        ('ghosted', 'Ghosted'),
        ('follow_up', 'Follow Up'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='applications')
    job_title = models.CharField(max_length=255)
    salary_range = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Applied')
    date_applied = models.DateField()
    notes = models.TextField(blank=True, null=True)
    recruiter = models.ForeignKey('Contact', on_delete=models.SET_NULL, null=True, blank=True, related_name='recruited_applications')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.job_title} at {self.company.name}"
    

class Interview(models.Model):

    INTERVIEW_TYPES = [
        ('Human Resources', 'Human Resources'),
        ('Design Interview', 'Design Interview'),
        ('Technical Interview', 'Technical Interview'),
        ('Technical Hands On', 'Technical Hands On'),
        ('Final', 'Final'),
    ]

    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='interviews')
    interview_type = models.CharField(max_length=50, choices=INTERVIEW_TYPES)
    date = models.DateTimeField()
    notes = models.TextField(blank=True, null=True)
    result = models.CharField(max_length=100, blank=True, null=True)
    interviewers = models.ManyToManyField('Contact', blank=True, related_name='conducted_interviews')

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.interview_type} - {self.application.job_title}"
