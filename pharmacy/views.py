from django.contrib import messages
from django.db.models import Count, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.decorators import role_required
from .forms import MedicineForm, PharmacyForm
from .models import Medicine, Pharmacy


# ---------------------------------------------------------------- Medicine Seeker
@role_required('seeker')
def medicine_search(request):
    meds = Medicine.objects.filter(pharmacy__is_active=True).select_related('pharmacy')
    q = request.GET.get('q', '').strip()
    status = request.GET.get('status', '')
    pharmacy_id = request.GET.get('pharmacy', '')
    location = request.GET.get('location', '').strip()

    if q:
        meds = meds.filter(Q(name__icontains=q) | Q(generic_name__icontains=q))
    if status in dict(Medicine.STATUS_CHOICES):
        meds = meds.filter(status=status)
    if pharmacy_id.isdigit():
        meds = meds.filter(pharmacy_id=int(pharmacy_id))
    if location:
        meds = meds.filter(pharmacy__location__icontains=location)

    return render(request, 'pharmacy/medicine_search.html', {
        'medicines': meds,
        'pharmacies': Pharmacy.objects.filter(is_active=True),
        'statuses': Medicine.STATUS_CHOICES,
        'q': q, 'status': status, 'pharmacy_id': pharmacy_id, 'location': location,
    })


# ---------------------------------------------------------------- Pharmacist
def _my_pharmacy(user):
    return Pharmacy.objects.filter(owner=user).first()


@role_required('pharmacist')
def my_pharmacy(request):
    """Create or update the pharmacist's own pharmacy profile."""
    pharmacy = _my_pharmacy(request.user)
    form = PharmacyForm(request.POST or None, instance=pharmacy)
    if request.method == 'POST':
        if form.is_valid():
            obj = form.save(commit=False)
            obj.owner = request.user
            obj.save()
            messages.success(request, "Pharmacy profile saved.")
            return redirect('pharmacist_medicines')
        messages.error(request, "Please fix the errors below.")
    title = "Edit My Pharmacy" if pharmacy else "Set Up Your Pharmacy"
    return render(request, 'pharmacy/form.html', {'form': form, 'title': title, 'back_url': 'dashboard'})


@role_required('pharmacist')
def pharmacist_medicines(request):
    pharmacy = _my_pharmacy(request.user)
    if not pharmacy:
        messages.error(request, "Set up your pharmacy profile before listing medicines.")
        return redirect('my_pharmacy')
    meds = pharmacy.medicines.all()
    q = request.GET.get('q', '').strip()
    if q:
        meds = meds.filter(Q(name__icontains=q) | Q(generic_name__icontains=q))
    return render(request, 'pharmacy/pharmacist_medicines.html', {
        'pharmacy': pharmacy, 'medicines': meds, 'q': q, 'statuses': Medicine.STATUS_CHOICES})


@role_required('pharmacist')
def medicine_create(request):
    pharmacy = _my_pharmacy(request.user)
    if not pharmacy:
        messages.error(request, "Set up your pharmacy profile before listing medicines.")
        return redirect('my_pharmacy')
    form = MedicineForm(request.POST or None, pharmacy=pharmacy)
    if request.method == 'POST':
        if form.is_valid():
            m = form.save(commit=False)
            m.pharmacy = pharmacy
            m.availability_updated_at = timezone.now()
            m.save()
            messages.success(request, f"{m} added to your listing.")
            return redirect('pharmacist_medicines')
        messages.error(request, "Please fix the errors below.")
    return render(request, 'pharmacy/form.html', {
        'form': form, 'title': "Add Medicine", 'back_url': 'pharmacist_medicines'})


@role_required('pharmacist')
def medicine_edit(request, pk):
    m = get_object_or_404(Medicine, pk=pk, pharmacy__owner=request.user)
    form = MedicineForm(request.POST or None, instance=m)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, f"{m} updated.")
            return redirect('pharmacist_medicines')
        messages.error(request, "Please fix the errors below.")
    return render(request, 'pharmacy/form.html', {
        'form': form, 'title': f"Edit {m}", 'back_url': 'pharmacist_medicines'})


@role_required('pharmacist')
@require_POST
def medicine_status(request, pk):
    """Quick availability update; always refreshes the 'last updated' time."""
    m = get_object_or_404(Medicine, pk=pk, pharmacy__owner=request.user)
    new_status = request.POST.get('status')
    if new_status not in dict(Medicine.STATUS_CHOICES):
        messages.error(request, "Invalid availability status.")
        return redirect('pharmacist_medicines')
    m.status = new_status
    m.availability_updated_at = timezone.now()
    m.save()
    messages.success(request, f"{m} marked as {m.get_status_display()}.")
    return redirect('pharmacist_medicines')


@role_required('pharmacist')
@require_POST
def medicine_delete(request, pk):
    m = get_object_or_404(Medicine, pk=pk, pharmacy__owner=request.user)
    name = str(m)
    m.delete()
    messages.success(request, f"{name} removed from your listing.")
    return redirect('pharmacist_medicines')


# ---------------------------------------------------------------- Admin
@role_required('admin')
def admin_pharmacies(request):
    items = Pharmacy.objects.select_related('owner').annotate(med_count=Count('medicines'))
    return render(request, 'pharmacy/admin_pharmacies.html', {'pharmacies': items})


@role_required('admin')
@require_POST
def pharmacy_toggle(request, pk):
    p = get_object_or_404(Pharmacy, pk=pk)
    p.is_active = not p.is_active
    p.save()
    messages.success(request, f"{p.name} is now {'participating' if p.is_active else 'deactivated'}.")
    return redirect('admin_pharmacies')


@role_required('admin')
def admin_medicines(request):
    meds = Medicine.objects.select_related('pharmacy')
    q = request.GET.get('q', '').strip()
    if q:
        meds = meds.filter(Q(name__icontains=q) | Q(generic_name__icontains=q) | Q(pharmacy__name__icontains=q))
    return render(request, 'pharmacy/admin_medicines.html', {'medicines': meds, 'q': q})


@role_required('admin')
def admin_medicine_edit(request, pk):
    m = get_object_or_404(Medicine, pk=pk)
    form = MedicineForm(request.POST or None, instance=m)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, f"{m} updated.")
            return redirect('admin_medicines')
        messages.error(request, "Please fix the errors below.")
    return render(request, 'pharmacy/form.html', {
        'form': form, 'title': f"Edit {m} ({m.pharmacy.name})", 'back_url': 'admin_medicines'})


@role_required('admin')
@require_POST
def admin_medicine_delete(request, pk):
    m = get_object_or_404(Medicine, pk=pk)
    name = str(m)
    m.delete()
    messages.success(request, f"{name} deleted.")
    return redirect('admin_medicines')
