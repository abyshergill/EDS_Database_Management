import logging

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from .decorators import admin_required
from .forms import StyledSetPasswordForm, UserCreateForm, UserUpdateForm

User = get_user_model()
logger = logging.getLogger(__name__)


@admin_required
def user_list(request):
    query = request.GET.get("q", "").strip()
    users = User.objects.annotate(n_records=Count("records_created")).order_by("username")
    if query:
        users = users.filter(
            Q(username__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(email__icontains=query)
        )
    page = Paginator(users, 20).get_page(request.GET.get("page"))
    return render(request, "accounts/user_list.html", {"page": page, "query": query})


@admin_required
@require_http_methods(["GET", "POST"])
def user_create(request):
    form = UserCreateForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        logger.info("User %s created by admin %s (admin=%s)", user.username, request.user.username, user.is_staff)
        messages.success(request, f"Account “{user.username}” created.")
        return redirect("accounts:list")
    return render(request, "accounts/user_form.html", {"form": form, "is_new": True})


@admin_required
@require_http_methods(["GET", "POST"])
def user_update(request, pk):
    target = get_object_or_404(User, pk=pk)
    form = UserUpdateForm(request.POST or None, instance=target, acting_user=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        logger.info("User %s updated by admin %s: %s", target.username, request.user.username, form.changed_data)
        messages.success(request, f"Account “{target.username}” updated.")
        return redirect("accounts:list")
    return render(request, "accounts/user_form.html", {"form": form, "target": target, "is_new": False})


@admin_required
@require_http_methods(["GET", "POST"])
def user_set_password(request, pk):
    target = get_object_or_404(User, pk=pk)
    form = StyledSetPasswordForm(target, request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        logger.info("Password of %s reset by admin %s", target.username, request.user.username)
        messages.success(request, f"Password for “{target.username}” has been reset.")
        return redirect("accounts:list")
    return render(request, "accounts/user_password.html", {"form": form, "target": target})


@admin_required
@require_POST
def user_delete(request, pk):
    target = get_object_or_404(User, pk=pk)
    if target.pk == request.user.pk:
        messages.error(request, "You cannot delete your own account.")
        return redirect("accounts:list")
    username = target.username
    target.delete()  # records and history keep working (SET_NULL / stored username)
    logger.info("User %s deleted by admin %s", username, request.user.username)
    messages.success(request, f"Account “{username}” deleted.")
    return redirect("accounts:list")
