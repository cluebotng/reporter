import logging
from typing import Any

from django.core.management import BaseCommand
from django.db.models import Q

from cbng_reporter.constants import REPORT_INTERFACE_USERNAME, ReportStatus
from cbng_reporter.libs.reports import update_status
from cbng_reporter.models import Report, User

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args: Any, **options: Any) -> None:
        """Send pending reports for edits by 'semi-trusted' users (admins) directly to the review interface."""
        trusted_usernames = set(
            User.objects.filter(Q(is_admin=True) | Q(is_superadmin=True)).values_list("username", flat=True)
        )

        for report in Report.objects.select_related("vandalism").filter(status=ReportStatus.REPORTED):
            username = report.vandalism.user
            if username in trusted_usernames:
                logger.info(f"Sending {report.vandalism_id} ({username}) to review interface")
                update_status(report, ReportStatus.SENT_TO_REVIEW, REPORT_INTERFACE_USERNAME)
