from django.urls import path
from django.shortcuts import redirect
from . import views
from .decorators import home_for


def dashboard_router(request):
    if not request.user.is_authenticated:
        return redirect('login')
    return redirect(home_for(request.user))


urlpatterns = [
    path('', dashboard_router, name='home'),
    path('dashboard/', dashboard_router, name='dashboard'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('patient-dashboard/', views.patient_dashboard_view, name='patient_dashboard'),
    path('pharmacist-dashboard/', views.pharmacist_dashboard_view, name='pharmacist_dashboard'),
    path('admin-dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('profile/', views.profile_view, name='profile'),
]
