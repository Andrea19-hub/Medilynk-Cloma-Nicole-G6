from django.urls import path
from . import views
from django.shortcuts import redirect

def dashboard_router(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if getattr(request.user, 'role', None) == 'admin' or request.user.is_staff or request.user.is_superuser:
        return redirect('admin_dashboard')
    return redirect('patient_dashboard')

urlpatterns = [
    path('', dashboard_router, name='home'),
    path('dashboard/', dashboard_router, name='dashboard'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('patient-dashboard/', views.patient_dashboard_view, name='patient_dashboard'),
    path('admin-dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('profile/', views.profile_view, name='profile'),
]