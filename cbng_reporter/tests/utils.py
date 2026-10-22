import itertools
from unittest import mock

from cbng_reporter.constants import ReportStatus
from cbng_reporter.models import Report, User, Vandalism

_ids = itertools.count(1000)


def create_vandalism(**kwargs) -> Vandalism:
    new_id = next(_ids)
    with mock.patch.object(Vandalism, "read_only", False):
        return Vandalism.objects.create(
            **{
                "user": "Some Editor",
                "article": "Some Article",
                "heuristic": "",
                "reason": "ANN scored at 0.951234",
                "diff": f"https://en.wikipedia.org/w/index.php?diff={new_id}",
                "old_id": new_id - 1,
                "new_id": new_id,
                "reverted": True,
            }
            | kwargs
        )


def create_report(vandalism: Vandalism | None = None, user: User | None = None, **kwargs) -> Report:
    return Report.objects.create(
        **{
            "vandalism": vandalism or create_vandalism(),
            "reporter_id": user.id if user else -1,
            "reporter": user.username if user else "Anonymous",
            "status": ReportStatus.REPORTED,
        }
        | kwargs
    )


def create_user(username: str = "Test User", **kwargs) -> User:
    return User.objects.create(username=username, **kwargs)
