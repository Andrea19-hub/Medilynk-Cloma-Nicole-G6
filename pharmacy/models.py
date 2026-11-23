from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone

phone_validator = RegexValidator(
    r'^[0-9+\-\s()]{7,20}$',
    "Enter a valid contact number (digits, spaces, +, -, parentheses; 7-20 characters).",
)


class Pharmacy(models.Model):
    """A participating pharmacy. One pharmacist account owns one pharmacy."""
    owner = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='pharmacy')
    name = models.CharField(max_length=120, unique=True)
    location = models.CharField(max_length=200, help_text="General location, e.g. barangay and city")
    contact_number = models.CharField(max_length=20, blank=True, validators=[phone_validator])
    is_active = models.BooleanField(default=True, help_text="Participating pharmacies are visible to medicine seekers")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'pharmacies'

    def __str__(self):
        return self.name


class Medicine(models.Model):
    """A medicine listed by a pharmacy, with its current availability."""
    STATUS_CHOICES = (
        ('available', 'Available'),
        ('low_stock', 'Low Stock'),
        ('out_of_stock', 'Out of Stock'),
    )
    BADGES = {'available': 'success', 'low_stock': 'warning text-dark', 'out_of_stock': 'danger'}

    pharmacy = models.ForeignKey(Pharmacy, on_delete=models.CASCADE, related_name='medicines')
    name = models.CharField(max_length=120)
    generic_name = models.CharField(max_length=120, blank=True)
    strength = models.CharField(max_length=50, blank=True, help_text="e.g. 500mg")
    description = models.TextField(blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='available')
    availability_updated_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} {self.strength}".strip()

    @property
    def badge(self):
        return self.BADGES.get(self.status, 'secondary')

    def save(self, *args, **kwargs):
        # Any change of status refreshes the "last availability update" timestamp.
        if self.pk:
            old = Medicine.objects.filter(pk=self.pk).values_list('status', flat=True).first()
            if old is not None and old != self.status:
                self.availability_updated_at = timezone.now()
        super().save(*args, **kwargs)
