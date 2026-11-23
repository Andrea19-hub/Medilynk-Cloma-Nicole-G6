from django import forms
from .models import Medicine, Pharmacy


class BootstrapMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            css = 'form-select' if isinstance(f.widget, forms.Select) else 'form-control'
            f.widget.attrs.setdefault('class', css)


class PharmacyForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Pharmacy
        fields = ['name', 'location', 'contact_number']

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if len(name) < 3:
            raise forms.ValidationError("Pharmacy name must be at least 3 characters.")
        qs = Pharmacy.objects.filter(name__iexact=name)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("A pharmacy with this name already exists.")
        return name

    def clean_location(self):
        loc = self.cleaned_data['location'].strip()
        if len(loc) < 3:
            raise forms.ValidationError("Please enter a general location (e.g. barangay, city).")
        return loc


class MedicineForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Medicine
        fields = ['name', 'generic_name', 'strength', 'description', 'status']
        widgets = {'description': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, pharmacy=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.pharmacy = pharmacy or getattr(self.instance, 'pharmacy', None)

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if len(name) < 2:
            raise forms.ValidationError("Medicine name must be at least 2 characters.")
        return name

    def clean(self):
        cleaned = super().clean()
        name = cleaned.get('name')
        if name and self.pharmacy:
            dup = Medicine.objects.filter(
                pharmacy=self.pharmacy, name__iexact=name,
                strength__iexact=(cleaned.get('strength') or '').strip())
            if self.instance.pk:
                dup = dup.exclude(pk=self.instance.pk)
            if dup.exists():
                self.add_error('name', "This pharmacy already lists this medicine with the same strength.")
        return cleaned
