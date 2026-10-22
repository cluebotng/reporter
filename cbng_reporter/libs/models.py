from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SocialLogin:
    """Stand in for `UserSocialAuth`, social auth only needs the provider to complete the login"""

    provider: str
    uid: str


@dataclass
class Revision:
    id: int
    user: str | None
    timestamp: datetime | None
    comment: str | None


@dataclass
class Diff:
    html: str
    old: Revision
    new: Revision

    @property
    def revisions(self) -> tuple[Revision, Revision]:
        return self.old, self.new


@dataclass
class ImportResult:
    processed_groups: list[int] = field(default_factory=list)
    expected_statuses: dict[int, int] = field(default_factory=dict)
    updated_edit_ids: list[int] = field(default_factory=list)
