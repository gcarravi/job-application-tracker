from django import forms
from .models import Application, Company

class ApplicationForm(forms.ModelForm):

    class Meta:
        model = Application
        fields = [
            "company",
            "job_title",
            "salary_range",
            "status",
            "date_applied",
            "notes",
        ]
        widgets = {
            "date_applied": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        if user:
            self.fields["company"].queryset = Company.objects.filter(user=user)

        # Add Bootstrap class to every field
        for field in self.fields.values():
            field.widget.attrs.update({"class": "form-control"})