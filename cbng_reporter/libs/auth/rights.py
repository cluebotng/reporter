import logging

from cbng_reporter.constants import MANAGE_REPORTS_PERMISSION
from cbng_reporter.libs.wikipedia import WikipediaReader
from cbng_reporter.models import User

logger = logging.getLogger(__name__)


class AutoAdminRightsChecker:
    def __init__(self):
        self._wikipedia_reader = WikipediaReader()

    def execute(self, user: User):
        if user.has_perm(MANAGE_REPORTS_PERMISSION):
            logger.debug(f"{user.username} already has admin access")
            return

        if self._wikipedia_reader.user_has_elevated_rights(user.username):
            logger.info(f"Marking {user.username} as an admin: user has elevated wiki rights")
            user.is_admin = True
            user.save(update_fields=["is_admin"])
