import hmac

from django.conf import settings
from django.contrib import auth, messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render, resolve_url
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST, require_safe
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from cbng_reporter.constants import (
    ANONYMOUS_USERNAME,
    MANAGE_REPORTS_PERMISSION,
    MANAGE_USERS_PERMISSION,
    OPEN_REPORT_STATUSES,
    ReportStatus,
)
from cbng_reporter.forms import CommentForm, OptionsForm, ReportForm, RevertLookupForm, StatusForm
from cbng_reporter.legacy import legacy_page_redirect
from cbng_reporter.libs.metrics import MetricsExporter
from cbng_reporter.libs.reports import create_comment, create_report, get_next_pending_report, update_status
from cbng_reporter.libs.wikipedia import WikipediaReader
from cbng_reporter.models import Comment, Report, User, Vandalism

STATUS_ACTIONS = [
    (ReportStatus.REPORTED, "Reported", "r", "r"),
    (ReportStatus.INVALID, "Invalid", "i|<", "i ArrowLeft"),
    (ReportStatus.SENT_TO_REVIEW, "Defer to Review Interface", "d|>", "d ArrowRight"),
    (ReportStatus.BUG, "Bug", "b|^", "b ArrowUp"),
    (ReportStatus.RESOLVED, "Resolved", None, None),
]


def home(request):
    if response := legacy_page_redirect(request):
        return response

    return render(request, "cbng_reporter/home.html", {"form": RevertLookupForm()})


@require_safe
def login(request):
    next_url = request.GET.get("next", "")
    if not url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        next_url = ""

    if request.user.is_authenticated:
        return redirect(next_url or resolve_url(settings.LOGIN_REDIRECT_URL))

    return render(request, "cbng_reporter/login.html", {"next_url": next_url})


@require_POST
def logout(request):
    auth.logout(request)
    return redirect("report-list")


@require_safe
def metrics(request):
    if settings.MONITORING_SHARED_SECRET and not hmac.compare_digest(
        request.headers.get("Authorization", "").encode(), f"Bearer {settings.MONITORING_SHARED_SECRET}".encode()
    ):
        return HttpResponseForbidden()

    MetricsExporter().update_metrics()
    return HttpResponse(content=generate_latest(), content_type=CONTENT_TYPE_LATEST)


@require_safe
def report_lookup(request):
    form = RevertLookupForm(request.GET)
    if form.is_valid():
        return redirect("report", id=form.cleaned_data["id"])

    messages.error(request, "Please enter a valid revert ID.")
    return redirect("home")


def report(request, id: int):
    vandalism = Vandalism.objects.filter(id=id).first()
    if not vandalism:
        messages.error(request, f"No revert found with ID {id}.")
        return redirect("home")

    if Report.objects.filter(vandalism=vandalism).exists():
        return redirect("report-view", id=vandalism.id)

    form = ReportForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            create_report(vandalism, request.user, form.cleaned_data["comment"])
        except IntegrityError:
            pass
        return redirect("report-view", id=vandalism.id)

    return render(
        request,
        "cbng_reporter/report.html",
        {
            "vandalism": vandalism,
            "diff": WikipediaReader().get_diff(vandalism.new_id),
            "form": form,
        },
    )


@require_safe
def report_list(request):
    show_all = request.GET.get("show_all") == "1"
    hide_anonymous = not show_all and request.user.is_authenticated and bool(request.user.hide_anon)

    reports = Report.objects.all()
    if not show_all:
        reports = reports.filter(status__in=OPEN_REPORT_STATUSES)
    if hide_anonymous:
        reports = reports.exclude(reporter__icontains=ANONYMOUS_USERNAME)

    paginator = Paginator(reports.order_by("status", "vandalism_id"), settings.CBNG_REPORTS_PER_PAGE)
    return render(
        request,
        "cbng_reporter/list.html",
        {
            "page_obj": paginator.get_page(request.GET.get("page")),
            "show_all": show_all,
            "hide_anonymous": hide_anonymous,
        },
    )


@require_safe
def report_view(request, id: int):
    vandalism = Vandalism.objects.filter(id=id).first()
    if not vandalism:
        return redirect("report-list")

    report = Report.objects.filter(vandalism=vandalism).first()
    if not report:
        return redirect("report", id=vandalism.id)

    comments = list(report.comments.all())
    authors = User.objects.in_bulk({comment.user_id for comment in comments if comment.user_id > 0})
    for comment in comments:
        comment.author = authors.get(comment.user_id)

    return render(
        request,
        "cbng_reporter/view.html",
        {
            "vandalism": vandalism,
            "diff": WikipediaReader().get_diff(vandalism.new_id),
            "report": report,
            "comments": comments,
            "comment_form": CommentForm(),
            "status_actions": STATUS_ACTIONS,
        },
    )


@require_safe
def report_by_revision(request, new_id: int):
    if vandalism := Vandalism.objects.filter(new_id=new_id).order_by("id").first():
        return redirect("report-view", id=vandalism.id)
    return redirect("report-list")


@require_POST
@login_required
def report_comment(request, id: int):
    report = get_object_or_404(Report, vandalism_id=id)
    form = CommentForm(request.POST)
    if form.is_valid():
        create_comment(report, request.user, form.cleaned_data["comment"])
    return redirect("report-view", id=id)


@require_POST
@login_required
@permission_required(MANAGE_REPORTS_PERMISSION, raise_exception=True)
def report_status(request, id: int):
    report = get_object_or_404(Report, vandalism_id=id)
    form = StatusForm(request.POST)
    if not form.is_valid():
        return HttpResponseBadRequest("Invalid status")

    update_status(report, form.cleaned_data["status"], request.user.username, request.user)

    if request.user.next_on_review and (
        next_report := get_next_pending_report(exclude_anonymous=bool(request.user.hide_anon))
    ):
        return redirect("report-view", id=next_report.vandalism_id)

    return redirect("report-view", id=id)


@require_POST
@login_required
@permission_required(MANAGE_USERS_PERMISSION, raise_exception=True)
def report_comment_delete(request, id: int, comment_id: int):
    get_object_or_404(Comment, report_id=id, id=comment_id).delete()
    return redirect("report-view", id=id)


@login_required
def options(request):
    form = OptionsForm(request.POST or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save(commit=False).save(update_fields=OptionsForm.Meta.fields)
        messages.success(request, "Saved!")
        return redirect("options")

    return render(request, "cbng_reporter/options.html", {"form": form})
