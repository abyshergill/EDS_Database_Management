import mimetypes
import re
from pathlib import Path

from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST

from accounts.decorators import admin_required

from . import history
from .forms import EDSRecordForm
from .models import EDSRecord, RecordHistory

PAGE_SIZE = 15


def _delete_files_on_commit(names, storage):
    names = [n for n in names if n]
    if names:
        transaction.on_commit(lambda: [storage.delete(n) for n in names])


def record_list(request):
    query = request.GET.get("q", "").strip()
    records = EDSRecord.objects.select_related("created_by", "modified_by")
    if query:
        records = records.filter(
            Q(component__icontains=query)
            | Q(remark__icontains=query)
            | Q(vhx_remark__icontains=query)
            | Q(eds_remark__icontains=query)
        )
    page = Paginator(records, PAGE_SIZE).get_page(request.GET.get("page"))

    week_ago = timezone.now() - timezone.timedelta(days=7)
    stats = {
        "total": EDSRecord.objects.count(),
        "this_week": EDSRecord.objects.filter(created_at__gte=week_ago).count(),
        "with_images": EDSRecord.objects.exclude(vhx_image="", eds_image="").count(),
        "changes_week": RecordHistory.objects.filter(timestamp__gte=week_ago).count(),
    }
    return render(
        request,
        "records/record_list.html",
        {"page": page, "query": query, "stats": stats},
    )


def record_detail(request, pk):
    record = get_object_or_404(EDSRecord.objects.select_related("created_by", "modified_by"), pk=pk)
    entries = RecordHistory.objects.filter(record_ref=record.pk).select_related("user")
    return render(request, "records/record_detail.html", {"record": record, "history": entries})


@require_http_methods(["GET", "POST"])
def record_create(request):
    form = EDSRecordForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            record = form.save(commit=False)
            record.created_by = request.user
            record.modified_by = request.user
            record.save()
            history.log_create(record, request.user)
        messages.success(request, f"Record “{record.component}” created.")
        return redirect(record)
    return render(request, "records/record_form.html", {"form": form, "is_new": True})


@require_http_methods(["GET", "POST"])
def record_update(request, pk):
    record = get_object_or_404(EDSRecord, pk=pk)
    before = history.snapshot(record)
    form = EDSRecordForm(request.POST or None, request.FILES or None, instance=record)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            record = form.save(commit=False)
            record.modified_by = request.user
            record.save()
            entry = history.log_update(record, request.user, before)
            # Remove image files that were replaced or cleared.
            stale = [
                before[f] for f in EDSRecord.IMAGE_FIELDS if before[f] and before[f] != getattr(record, f).name
            ]
            _delete_files_on_commit(stale, record.vhx_image.storage)
        if entry:
            messages.success(request, f"Record “{record.component}” updated.")
        else:
            messages.info(request, "No changes were made.")
        return redirect(record)
    return render(request, "records/record_form.html", {"form": form, "record": record, "is_new": False})


@require_POST
def record_delete(request, pk):
    record = get_object_or_404(EDSRecord, pk=pk)
    name = record.component
    with transaction.atomic():
        history.log_delete(record, request.user)
        files = [getattr(record, f).name for f in EDSRecord.IMAGE_FIELDS]
        storage = record.vhx_image.storage
        record.delete()
        _delete_files_on_commit(files, storage)
    messages.success(request, f"Record “{name}” deleted.")
    return redirect("records:list")


def record_image(request, pk, kind):
    """Serve a record image only to authenticated users (login enforced by middleware)."""
    record = get_object_or_404(EDSRecord, pk=pk)
    field = {"vhx": record.vhx_image, "eds": record.eds_image}.get(kind)
    if not field:
        raise Http404("No image")
    try:
        fh = field.open("rb")
    except FileNotFoundError:
        raise Http404("Image file missing")
    ext = Path(field.name).suffix
    download = request.GET.get("download") == "1"
    safe_component = re.sub(r"[^A-Za-z0-9._-]+", "_", record.component).strip("._") or "record"
    filename = f"{safe_component[:100]}_{kind.upper()}{ext}"
    content_type = mimetypes.guess_type(field.name)[0] or "application/octet-stream"
    return FileResponse(fh, as_attachment=download, filename=filename, content_type=content_type)


@admin_required
def activity_log(request):
    entries = RecordHistory.objects.select_related("user")
    action = request.GET.get("action", "")
    user_q = request.GET.get("user", "").strip()
    query = request.GET.get("q", "").strip()
    if action in RecordHistory.Action.values:
        entries = entries.filter(action=action)
    if user_q:
        entries = entries.filter(username__icontains=user_q)
    if query:
        entries = entries.filter(component__icontains=query)
    page = Paginator(entries, 25).get_page(request.GET.get("page"))
    top_users = (
        RecordHistory.objects.values("username").annotate(n=Count("id")).order_by("-n")[:5]
    )
    return render(
        request,
        "records/activity_log.html",
        {
            "page": page,
            "action": action,
            "user_q": user_q,
            "query": query,
            "actions": RecordHistory.Action.choices,
            "top_users": top_users,
        },
    )
