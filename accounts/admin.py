from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ['username', 'email', 'role', 'is_staff', 'is_active']
    list_filter = ['role', 'is_staff', 'is_active']
    fieldsets = UserAdmin.fieldsets + (
        ('Medilynk Profile Info', {'fields': ('role', 'phone_number', 'address', 'profile_picture')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Medilynk Profile Info', {'fields': ('email', 'role', 'phone_number', 'address')}),
    )


admin.site.register(User, CustomUserAdmin)