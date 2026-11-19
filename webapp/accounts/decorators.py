from functools import wraps

from django.core.exceptions import PermissionDenied


def is_app_admin(user):
    """An application admin is a staff user (or superuser)."""
    return user.is_authenticated and (user.is_staff or user.is_superuser)


def admin_required(view_func):
    """Allow only admins. Anonymous users are already redirected by the
    LoginRequiredMiddleware; logged-in non-admins get 403."""

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not is_app_admin(request.user):
            raise PermissionDenied("Administrator access required.")
        return view_func(request, *args, **kwargs)

    return wrapper
