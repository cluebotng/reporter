from django.db import models

ANONYMOUS_USER_ID = -1
SYSTEM_USER_ID = -2

ANONYMOUS_USERNAME = "Anonymous"
SYSTEM_USERNAME = "System"
REPORT_INTERFACE_USERNAME = "Report Interface"
REVIEW_INTERFACE_USERNAME = "Review Interface"

MANAGE_REPORTS_PERMISSION = "cbng_reporter.manage_reports"
MANAGE_USERS_PERMISSION = "cbng_reporter.manage_users"

ELEVATED_RIGHTS = {"rollback", "block", "deleterevision", "editprotected"}


class ReportStatus(models.IntegerChoices):
    REPORTED = 0, "Reported"
    INVALID = 1, "Invalid"
    SENT_TO_REVIEW = 2, "Sending to Review Interface"
    BUG = 3, "Bug"
    RESOLVED = 4, "Resolved"
    QUEUED_FOR_REVIEW = 5, "Queued to be reviewed"
    PARTIALLY_REVIEWED = 6, "Partially reviewed"
    REVIEWED_CONSTRUCTIVE = 7, "Reviewed - Included in dataset as Constructive"
    REVIEWED_VANDALISM = 8, "Reviewed - Included in dataset as Vandalism"
    REVIEWED_NOT_INCLUDED = 9, "Reviewed - Not included in dataset"
    EDIT_DATA_REMOVED = 10, "Edit Data Has Been Removed"


OPEN_REPORT_STATUSES = {
    ReportStatus.REPORTED,
    ReportStatus.SENT_TO_REVIEW,
    ReportStatus.BUG,
    ReportStatus.QUEUED_FOR_REVIEW,
    ReportStatus.PARTIALLY_REVIEWED,
}

REVIEW_EXPORT_STATUSES = {ReportStatus.SENT_TO_REVIEW}
REVIEW_EXPORT_IN_PROGRESS_STATUSES = {
    ReportStatus.SENT_TO_REVIEW,
    ReportStatus.QUEUED_FOR_REVIEW,
    ReportStatus.PARTIALLY_REVIEWED,
}

REVIEW_TO_REPORT_STATUS = {
    0: ReportStatus.QUEUED_FOR_REVIEW,
    1: ReportStatus.PARTIALLY_REVIEWED,
    2: ReportStatus.REVIEWED_VANDALISM,
    3: ReportStatus.REVIEWED_CONSTRUCTIVE,
    4: ReportStatus.REVIEWED_NOT_INCLUDED,
    5: ReportStatus.EDIT_DATA_REMOVED,
}
