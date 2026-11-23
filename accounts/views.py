from django.contrib import messages
from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect

from .decorators import role_required, home_for
from .forms import PatientRegistrationForm, UserProfileForm

User = get_user_model()


def register_view(request):
    if request.user.is_authenticated:
        return redirect(home_for(request.user))
    if request.method == 'POST':
        form = PatientRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.role = form.cleaned_data['role']
            user.save()
            login(request, user)
            messages.success(request, "Account created. Welcome to Medilynk!")
            return redirect(home_for(user))
        messages.error(request, "Please fix the errors below.")
    else:
        form = PatientRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect(home_for(request.user))
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect(home_for(user))
        messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect('login')


@login_required
def profile_view(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
            return redirect('profile')
        messages.error(request, "Please fix the errors below.")
    else:
        form = UserProfileForm(instance=request.user)
    return render(request, 'accounts/profile.html', {'form': form})


@role_required('seeker')
def patient_dashboard_view(request):
    from pharmacy.models import Medicine, Pharmacy
    visible = Medicine.objects.filter(pharmacy__is_active=True)
    return render(request, 'accounts/patient_dashboard.html', {
        'pharmacy_count': Pharmacy.objects.filter(is_active=True).count(),
        'listed_count': visible.count(),
        'available_count': visible.filter(status='available').count(),
    })


@role_required('pharmacist')
def pharmacist_dashboard_view(request):
    from pharmacy.models import Pharmacy
    pharmacy = Pharmacy.objects.filter(owner=request.user).first()
    ctx = {'pharmacy': pharmacy}
    if pharmacy:
        meds = pharmacy.medicines.all()
        ctx.update({
            'total': meds.count(),
            'available': meds.filter(status='available').count(),
            'low_stock': meds.filter(status='low_stock').count(),
            'out_of_stock': meds.filter(status='out_of_stock').count(),
        })
    return render(request, 'accounts/pharmacist_dashboard.html', ctx)


@role_required('admin')
def admin_dashboard_view(request):
    from pharmacy.models import Medicine, Pharmacy
    return render(request, 'accounts/admin_dashboard.html', {
        'total_patients': User.objects.filter(role='seeker').count(),
        'total_pharmacists': User.objects.filter(role='pharmacist').count(),
        'total_pharmacies': Pharmacy.objects.count(),
        'total_medicines': Medicine.objects.count(),
    })
