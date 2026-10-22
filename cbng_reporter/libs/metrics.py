import logging

from django.conf import settings
from django.db.models import Count
from prometheus_client import Gauge

from cbng_reporter.constants import ReportStatus
from cbng_reporter.models import Beaten, Report, Vandalism

logger = logging.getLogger(__name__)

reports_by_status_count = Gauge(
    f"{settings.PROMETHEUS_METRIC_NAMESPACE}_reports_by_status_count",
    "Number of reports by status",
    ["status"],
)

vandalism_by_reverted_count = Gauge(
    f"{settings.PROMETHEUS_METRIC_NAMESPACE}_vandalism_by_reverted_count",
    "Number of vandalised edits detected, by if they were reverted",
    ["reverted"],
)

reverts_beaten_count = Gauge(
    f"{settings.PROMETHEUS_METRIC_NAMESPACE}_reverts_beaten_count",
    "Number of attempted reverts that were beaten",
)


class MetricsExporter:
    def _update_reports_by_status_count(self):
        counts_by_status = {
            row["status"]: row["count"] for row in Report.objects.values("status").annotate(count=Count("status"))
        }
        for status in ReportStatus:
            reports_by_status_count.labels(status=status.label).set(counts_by_status.get(status.value, 0))

    def _update_vandalism_by_reverted_count(self):
        counts_by_reverted = {
            row["reverted"]: row["count"] for row in Vandalism.objects.values("reverted").annotate(count=Count("id"))
        }
        for reverted in (False, True):
            vandalism_by_reverted_count.labels(reverted=f"{reverted}".lower()).set(counts_by_reverted.get(reverted, 0))

    def _update_reverts_beaten_count(self):
        reverts_beaten_count.set(Beaten.objects.count())

    def update_metrics(self):
        self._update_reports_by_status_count()
        self._update_vandalism_by_reverted_count()
        self._update_reverts_beaten_count()
