from django.contrib.auth.models import AnonymousUser
from django.test import TestCase

from cbng_reporter.constants import ReportStatus
from cbng_reporter.libs.reports import create_report, update_status
from cbng_reporter.models import EditSentForReview
from cbng_reporter.tests.utils import create_user, create_vandalism


class ReportsTestCase(TestCase):
    def testCreateReport(self):
        report = create_report(create_vandalism(), AnonymousUser(), "This was fine")
        self.assertEqual((report.reporter, report.status), ("Anonymous", ReportStatus.REPORTED))
        self.assertEqual(list(report.comments.values_list("username", "comment")), [("Anonymous", "This was fine")])

    def testStatusChangeAddsComment(self):
        user = create_user()
        report = create_report(create_vandalism(), AnonymousUser())
        update_status(report, ReportStatus.SENT_TO_REVIEW, user.username, user)

        self.assertEqual(
            list(report.comments.values_list("username", "comment")),
            [("System", f'{user.username} has marked this report as "Sending to Review Interface".')],
        )
        self.assertTrue(EditSentForReview.objects.filter(vandalism=report.vandalism, user_id=user.id).exists())

    def testTrustedEditorSentToReview(self):
        create_user("Trusted Editor", is_admin=True)
        report = create_report(create_vandalism(user="Trusted Editor"), AnonymousUser())

        self.assertEqual(report.status, ReportStatus.SENT_TO_REVIEW)
        self.assertEqual(
            list(report.comments.values_list("comment", flat=True)),
            ['Report Interface has marked this report as "Sending to Review Interface".'],
        )
