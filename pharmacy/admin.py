from django.contrib import admin
from .models import Medicine, Pharmacy


@admin.register(Pharmacy)
class PharmacyAdmin(admin.ModelAdmin):
    list_display = ['name', 'location', 'owner', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'location']


@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ['name', 'strength', 'pharmacy', 'status', 'availability_updated_at']
    list_filter = ['status', 'pharmacy']
    search_fields = ['name', 'generic_name']
