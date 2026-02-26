from django.contrib import admin
from  .models import Company, Application, Interview

# Register your models here.
admin.site.register(Company)
admin.site.register(Application)
admin.site.register(Interview)
