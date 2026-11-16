from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib.auth.forms import AuthenticationForm
from .forms import PatientRegistrationForm, UserProfileForm

User = get_user_model()

def register_view(request):
    if request.user.is_authenticated:
        return redirect('patient_dashboard')
    if request.method == 'POST':
        form = PatientRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.role = 'patient'
            user.save()
            login(request, user)
            return redirect('patient_dashboard')
    else:
        form = PatientRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        if getattr(request.user, 'role', None) == 'admin' or request.user.is_staff or request.user.is_superuser:
            return redirect('admin_dashboard')
        return redirect('patient_dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if getattr(user, 'role', None) == 'admin' or user.is_staff or user.is_superuser:
                return redirect('admin_dashboard')
            return redirect('patient_dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def profile_view(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = UserProfileForm(instance=request.user)
    return render(request, 'accounts/profile.html', {'form': form})

@login_required
def patient_dashboard_view(request):
    if getattr(request.user, 'role', None) != 'patient':
        raise PermissionDenied("Patients only.")
    return render(request, 'accounts/patient_dashboard.html')

@login_required
def admin_dashboard_view(request):
    if not (getattr(request.user, 'role', None) == 'admin' or request.user.is_staff or request.user.is_superuser):
        raise PermissionDenied("Admins only.")
    
    # Kuhaon ang total users para makita sa admin overview
    total_patients = User.objects.filter(role='patient').count()
    total_users = User.objects.count()
    
    context = {
        'total_patients': total_patients,
        'total_users': total_users,
    }
    return render(request, 'accounts/admin_dashboard.html', context)