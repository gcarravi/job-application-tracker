from django import forms
from .models import Application, Company


class ApplicationForm(forms.ModelForm):

    company_name = forms.CharField(
        max_length=255,
        label="Company Name",
    )
    company_location = forms.CharField(
        max_length=255,
        required=False,
        label="Location",
    )
    company_website = forms.URLField(
        required=False,
        label="Website",
    )

    class Meta:
        model = Application
        fields = [
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
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # Re-order so company fields appear first
        field_order = ["company_name", "company_location", "company_website",
                       "job_title", "salary_range", "status", "date_applied", "notes"]
        self.fields = {k: self.fields[k] for k in field_order}

        # Add form-control class to every field
        for field in self.fields.values():
            field.widget.attrs.update({"class": "form-control"})

    def save(self, commit=True):
        application = super().save(commit=False)
        if self.user:
            company, _ = Company.objects.get_or_create(
                user=self.user,
                name=self.cleaned_data["company_name"],
                defaults={
                    "location": self.cleaned_data.get("company_location", ""),
                    "website": self.cleaned_data.get("company_website", ""),
                },
            )
            application.company = company
        if commit:
            application.save()
        return application
