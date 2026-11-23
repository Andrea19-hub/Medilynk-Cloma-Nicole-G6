from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


def is_admin(user):
    return user.is_authenticated and (
        getattr(user, 'role', None) == 'admin' or user.is_staff or user.is_superuser
    )


def effective_role(user):
    return 'admin' if is_admin(user) else getattr(user, 'role', None)


def home_for(user):
    return {'admin': 'admin_dashboard', 'pharmacist': 'pharmacist_dashboard'}.get(
        effective_role(user), 'patient_dashboard')


def role_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            if effective_role(request.user) not in roles:
                raise PermissionDenied("You don't have access to this page.")
            return view(request, *args, **kwargs)
        return wrapper
    return decorator
