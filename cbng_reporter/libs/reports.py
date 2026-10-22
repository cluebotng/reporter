import logging

from django.contrib.auth.models import AnonymousUser
from django.db import transaction
from django.db.models import Q

from cbng_reporter.constants import (
    ANONYMOUS_USER_ID,
    ANONYMOUS_USERNAME,
    REPORT_INTERFACE_USERNAME,
    SYSTEM_USER_ID,
    SYSTEM_USERNAME,
    ReportStatus,
)
from cbng_reporter.models import Comment, EditSentForReview, Report, User, Vandalism

logger = logging.getLogger(__name__)


def _clean_text(text: str) -> str:
    return "".join(c if ord(c) <= 0xFFFF else "\ufffd" for c in text.replace("\r", ""))


def _user_details(user: User | AnonymousUser) -> tuple[int, str]:
    if user.is_authenticated:
        return user.id, user.username
    return ANONYMOUS_USER_ID, ANONYMOUS_USERNAME


def is_trusted_editor(username: str) -> bool:
    """
    Admin access is granted on login, by `sync_admin_rights` or by a human.

    The users table collation is case insensitive, but wiki usernames are not, so compare exactly.
    """
    return any(
        user.username == username
        for user in User.objects.filter(Q(is_admin=True) | Q(is_superadmin=True), username=username)
    )


def create_report(vandalism: Vandalism, user: User | AnonymousUser, comment: str | None = None) -> Report:
    reporter_id, reporter = _user_details(user)
    with transaction.atomic():
        report = Report.objects.create(
            vandalism=vandalism,
            reporter_id=reporter_id,
            reporter=reporter,
            status=ReportStatus.REPORTED,
        )
        if comment and comment.strip():
            create_comment(report, user, comment)
    logger.info(f"Created report for {vandalism.id} by {report.reporter}")

    if is_trusted_editor(vandalism.user):
        update_status(report, ReportStatus.SENT_TO_REVIEW, REPORT_INTERFACE_USERNAME)

    return report


def create_comment(report: Report, user: User | AnonymousUser, comment: str) -> Comment:
    user_id, username = _user_details(user)
    return Comment.objects.create(
        report=report,
        user_id=user_id,
        username=username,
        comment=_clean_text(comment),
    )


def update_status(report: Report, status: ReportStatus, actor_name: str, actor: User | AnonymousUser | None = None):
    status = ReportStatus(status)
    with transaction.atomic():
        report.status = status
        report.save(update_fields=["status"])

        Comment.objects.create(
            report=report,
            user_id=SYSTEM_USER_ID,
            username=SYSTEM_USERNAME,
            comment=f'{actor_name} has marked this report as "{status.label}".',
        )

        if status == ReportStatus.SENT_TO_REVIEW and actor is not None and actor.is_authenticated:
            EditSentForReview.objects.bulk_create(
                [EditSentForReview(vandalism_id=report.vandalism_id, user_id=actor.id)], ignore_conflicts=True
            )
    logger.info(f"Updated report {report.vandalism_id} to {status.label} by {actor_name}")


def get_next_pending_report(exclude_anonymous: bool) -> Report | None:
    reports = Report.objects.filter(status=ReportStatus.REPORTED)
    if exclude_anonymous:
        reports = reports.exclude(reporter__icontains=ANONYMOUS_USERNAME)
    return reports.order_by("vandalism_id").first()
