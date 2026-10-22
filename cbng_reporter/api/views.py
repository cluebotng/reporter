"""
API used by the review interface, the response formats match the legacy (PHP) API.
"""

from collections import defaultdict

from django.http import JsonResponse
from django.views.decorators.http import require_safe

from cbng_reporter.constants import REVIEW_EXPORT_IN_PROGRESS_STATUSES, REVIEW_EXPORT_STATUSES, ReportStatus
from cbng_reporter.models import EditSentForReview, Report, User


def _json_response(data) -> JsonResponse:
    return JsonResponse(data, safe=False, json_dumps_params={"indent": 4})


def _is_truthy(value: str | None) -> bool:
    return value is not None and value.lower() in {"1", "true", "yes"}


@require_safe
def review_export(request):
    statuses = (
        REVIEW_EXPORT_IN_PROGRESS_STATUSES
        if _is_truthy(request.GET.get("include_in_progress"))
        else REVIEW_EXPORT_STATUSES
    )
    return _json_response(
        list(
            Report.objects.filter(status__in=statuses)
            .order_by("vandalism_id")
            .values_list("vandalism__new_id", flat=True)
        )
    )


@require_safe
def review_export_users(request):
    usernames = dict(User.objects.values_list("id", "username"))

    edits = defaultdict(list)
    for entry in EditSentForReview.objects.select_related("vandalism").order_by("vandalism_id", "user_id"):
        if username := usernames.get(entry.user_id):
            edits[entry.vandalism.new_id].append(username)
    return _json_response(edits)


@require_safe
def statistics(request):
    return _json_response({"pending_reports": Report.objects.filter(status=ReportStatus.REPORTED).count()})
