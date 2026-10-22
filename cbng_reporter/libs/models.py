from dataclasses import dataclass
from datetime import datetime


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
