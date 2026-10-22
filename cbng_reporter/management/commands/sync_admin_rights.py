import logging
from typing import Any

from django.core.management import BaseCommand

from cbng_reporter.libs.auth.rights import AutoAdminRightsChecker
from cbng_reporter.models import User

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args: Any, **options: Any) -> None:
        """Grant admin access automatically, to users with elevated wiki rights."""
        checker = AutoAdminRightsChecker()
        for user in User.objects.filter(is_admin=False, is_superadmin=False):
            checker.execute(user)
