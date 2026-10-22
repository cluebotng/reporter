import logging
from datetime import datetime

import requests

from cbng_reporter.constants import ELEVATED_RIGHTS
from cbng_reporter.libs.models import Diff, Revision

logger = logging.getLogger(__name__)


def _parse_timestamp(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


class WikipediaReader:
    def __init__(self):
        self._session = requests.session()

    def get_user_rights(self, username: str) -> set[str] | None:
        try:
            r = self._session.get(
                "https://en.wikipedia.org/w/api.php",
                headers={
                    "User-Agent": "ClueBot NG Report Interface - Wikipedia - Fetch User Rights",
                },
                timeout=10,
                params={
                    "format": "json",
                    "action": "query",
                    "list": "users",
                    "usprop": "rights",
                    "ususers": username,
                },
            )
            r.raise_for_status()
            data = r.json()
        except (requests.RequestException, ValueError) as e:
            logger.warning(f"Failed to fetch user rights for {username}: {e}")
            return None

        if user_data := next(iter(data.get("query", {}).get("users", [])), None):
            return set(user_data.get("rights", []))
        return None

    def user_has_elevated_rights(self, username: str) -> bool:
        return bool((self.get_user_rights(username) or set()) & ELEVATED_RIGHTS)

    def get_diff(self, revision_id: int) -> Diff | None:
        """The diff of a revision against its parent, as shown by Wikipedia."""
        try:
            r = self._session.get(
                "https://en.wikipedia.org/w/api.php",
                headers={
                    "User-Agent": "ClueBot NG Report Interface - Wikipedia - Fetch Diff",
                },
                timeout=10,
                params={
                    "format": "json",
                    "formatversion": 2,
                    "action": "compare",
                    "fromrev": revision_id,
                    "torelative": "prev",
                    "prop": "diff|ids|user|comment|timestamp",
                },
            )
            r.raise_for_status()
            data = r.json()
        except (requests.RequestException, ValueError) as e:
            logger.warning(f"Failed to fetch diff for {revision_id}: {e}")
            return None

        compare = data.get("compare", {})
        if "error" in data or "body" not in compare:
            logger.info(f"No diff available for {revision_id}: {data.get('error', {}).get('code')}")
            return None

        return Diff(
            html=compare["body"],
            old=Revision(
                id=compare.get("fromrevid"),
                user=compare.get("fromuser"),
                timestamp=_parse_timestamp(compare.get("fromtimestamp")),
                comment=compare.get("fromcomment"),
            ),
            new=Revision(
                id=compare.get("torevid"),
                user=compare.get("touser"),
                timestamp=_parse_timestamp(compare.get("totimestamp")),
                comment=compare.get("tocomment"),
            ),
        )
