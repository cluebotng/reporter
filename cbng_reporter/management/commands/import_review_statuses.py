import logging
from typing import Any

from django.core.management import BaseCommand

from cbng_reporter.libs.review_interface import ReviewInterface

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args: Any, **options: Any) -> None:
        """Update report statuses from the review interface."""
        result = ReviewInterface().import_statuses()
        logger.info(
            f"Processed {len(result.processed_groups)} groups / {len(result.expected_statuses)} edits, "
            f"updated {len(result.updated_edit_ids)} reports"
        )
