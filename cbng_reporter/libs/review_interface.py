import logging

import requests
from django.conf import settings

from cbng_reporter.constants import REVIEW_INTERFACE_USERNAME, REVIEW_TO_REPORT_STATUS, ReportStatus
from cbng_reporter.libs.models import ImportResult
from cbng_reporter.libs.reports import update_status
from cbng_reporter.models import Report

logger = logging.getLogger(__name__)


class ReviewInterface:
    def __init__(self):
        self._session = requests.session()

    def _get(self, path: str):
        r = self._session.get(
            f"{settings.REVIEWER_URL}{path}",
            timeout=60,
            headers={
                "User-Agent": "ClueBot NG Report Interface - Review Import",
            },
        )
        r.raise_for_status()
        return r.json()

    def fetch_expected_statuses(self, result: ImportResult):
        for edit_group in self._get("/api/v1/edit-groups/"):
            if edit_group["type"] != "Reported False Positives":
                continue

            try:
                edit_statuses = self._get(f"/api/v1/edit-groups/{edit_group['id']}/dump-report-status/")
            except requests.RequestException as e:
                logger.warning(f"Failed to fetch report status for edit group {edit_group['id']}: {e}")
                continue

            result.processed_groups.append(edit_group["id"])
            for edit_id, review_status in edit_statuses.items():
                if report_status := REVIEW_TO_REPORT_STATUS.get(int(review_status)):
                    result.expected_statuses[int(edit_id)] = report_status

    def import_statuses(self) -> ImportResult:
        result = ImportResult()
        self.fetch_expected_statuses(result)

        edit_ids = list(result.expected_statuses.keys())
        for offset in range(0, len(edit_ids), 1000):
            reports = (
                Report.objects.select_related("vandalism")
                .exclude(
                    status__in={
                        ReportStatus.REPORTED,
                        ReportStatus.INVALID,
                        ReportStatus.BUG,
                        ReportStatus.RESOLVED,
                        ReportStatus.EDIT_DATA_REMOVED,
                    }
                )
                .filter(vandalism__new_id__in=edit_ids[offset : offset + 1000])
            )
            for report in reports:
                expected_status = result.expected_statuses[report.vandalism.new_id]
                if report.status != expected_status:
                    result.updated_edit_ids.append(report.vandalism.new_id)
                    update_status(report, expected_status, REVIEW_INTERFACE_USERNAME)

        return result
