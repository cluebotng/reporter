from django.test import TestCase

from cbng_reporter.constants import ReportStatus
from cbng_reporter.models import EditSentForReview
from cbng_reporter.tests.utils import create_report, create_user


class ApiTestCase(TestCase):
    def testExport(self):
        sent = create_report(status=ReportStatus.SENT_TO_REVIEW)
        queued = create_report(status=ReportStatus.QUEUED_FOR_REVIEW)
        partial = create_report(status=ReportStatus.PARTIALLY_REVIEWED)
        create_report(status=ReportStatus.REPORTED)

        self.assertEqual(self.client.get("/api/v1/review/export/").json(), [sent.vandalism.new_id])
        self.assertEqual(
            self.client.get("/api/v1/review/export/?include_in_progress=1").json(),
            [sent.vandalism.new_id, queued.vandalism.new_id, partial.vandalism.new_id],
        )

    def testExportUsers(self):
        user_1, user_2 = create_user("User 1"), create_user("User 2")
        report_1, report_2 = create_report(), create_report()
        EditSentForReview.objects.bulk_create(
            [
                EditSentForReview(vandalism=report_1.vandalism, user_id=user_1.id),
                EditSentForReview(vandalism=report_1.vandalism, user_id=user_2.id),
                EditSentForReview(vandalism=report_2.vandalism, user_id=user_2.id),
                EditSentForReview(vandalism=report_2.vandalism, user_id=-2),
            ]
        )

        self.assertEqual(
            self.client.get("/api/v1/review/export/users/").json(),
            {
                f"{report_1.vandalism.new_id}": ["User 1", "User 2"],
                f"{report_2.vandalism.new_id}": ["User 2"],
            },
        )

    def testStatistics(self):
        create_report()
        create_report(status=ReportStatus.SENT_TO_REVIEW)
        self.assertEqual(self.client.get("/api/v1/statistics/").json(), {"pending_reports": 1})
