"""
Role-based access decorators for CropConnect
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages


def role_required(*roles):
    """Decorator to restrict access by user role."""
    def decorator(view_func):
        @wraps(view_func)
        @login_required(login_url='/login/')
        def _wrapped_view(request, *args, **kwargs):
            if not hasattr(request.user, 'role') or request.user.role not in roles:
                messages.error(request, 'You do not have permission to access this page.')
                if hasattr(request.user, 'role'):
                    if request.user.role == 'FARMER':
                        return redirect('farmer_dashboard')
                    elif request.user.role == 'OFFICER':
                        return redirect('officer_dashboard')
                    elif request.user.role == 'ADMIN':
                        return redirect('admin_dashboard')
                return redirect('home')
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


farmer_required = role_required('FARMER')
officer_required = role_required('OFFICER')
admin_required = role_required('ADMIN')
