"""
Models for the bot database.

`vandalism` & `beaten` are written by the bot, they are not managed by us & are read only (`ReadOnlyModel`).

`reports`, `comments`, `users` & `edits_sent_for_review` are managed by us,
the initial migration matches the (pre-existing) legacy schema exactly.
"""

import logging
from typing import ClassVar

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import connection, models, transaction
from django.db.models.functions import Now
from django.utils.crypto import salted_hmac

from cbng_reporter.constants import ANONYMOUS_USER_ID, MANAGE_REPORTS_PERMISSION, ReportStatus

logger = logging.getLogger(__name__)


class ReadOnlyTableError(Exception):
    pass


class ReadOnlyQuerySet(models.QuerySet):
    def update(self, **kwargs):
        self.model.check_writable()
        return super().update(**kwargs)

    def bulk_update(self, *args, **kwargs):
        self.model.check_writable()
        return super().bulk_update(*args, **kwargs)

    def bulk_create(self, *args, **kwargs):
        self.model.check_writable()
        return super().bulk_create(*args, **kwargs)

    def delete(self):
        self.model.check_writable()
        return super().delete()

    delete.alters_data = True
    delete.queryset_only = True


class ReadOnlyModel(models.Model):
    """A table owned by the bot, which we must never write to."""

    read_only: ClassVar[bool] = True

    objects = ReadOnlyQuerySet.as_manager()

    class Meta:
        abstract = True
        managed = False

    @classmethod
    def check_writable(cls):
        if cls.read_only:
            raise ReadOnlyTableError(f"{cls._meta.db_table} is read only")

    def save(self, **kwargs):
        self.check_writable()
        super().save(**kwargs)

    def delete(self, *args, **kwargs):
        self.check_writable()
        return super().delete(*args, **kwargs)


class Vandalism(ReadOnlyModel):
    """Written by the bot for every revert"""

    id = models.AutoField(primary_key=True)
    timestamp = models.DateTimeField(db_default=Now())
    user = models.CharField(max_length=256)
    article = models.CharField(max_length=256)
    heuristic = models.CharField(max_length=64)
    regex = models.CharField(max_length=2048, null=True)
    reason = models.CharField(max_length=512)
    diff = models.CharField(max_length=512)
    old_id = models.IntegerField()
    new_id = models.IntegerField()
    reverted = models.BooleanField()

    class Meta(ReadOnlyModel.Meta):
        db_table = "vandalism"


class Beaten(ReadOnlyModel):
    """Written by the bot when a revert was beaten"""

    id = models.AutoField(primary_key=True)
    timestamp = models.DateTimeField(db_default=Now())
    article = models.CharField(max_length=256)
    diff = models.CharField(max_length=512)
    user = models.CharField(max_length=256)

    class Meta(ReadOnlyModel.Meta):
        db_table = "beaten"


class User(AbstractBaseUser):
    id = models.AutoField(primary_key=True, db_column="userid")
    username = models.CharField(max_length=128, unique=True)
    is_admin = models.BooleanField(default=False, db_column="admin")
    is_superadmin = models.BooleanField(default=False, db_column="superadmin")
    next_on_review = models.BooleanField(default=True, null=True)
    keyboard_shortcuts = models.BooleanField(default=True, null=True)
    hide_anon = models.BooleanField(default=False, null=True)

    password = None
    last_login = None

    objects = BaseUserManager()

    USERNAME_FIELD = "username"

    class Meta:
        db_table = "users"

    def has_perm(self, perm: str, obj=None) -> bool:
        if self.is_superadmin:
            return True
        return self.is_admin and perm == MANAGE_REPORTS_PERMISSION

    def has_perms(self, perm_list, obj=None) -> bool:
        return all(self.has_perm(perm, obj) for perm in perm_list)

    def has_module_perms(self, app_label: str) -> bool:
        return app_label == "cbng_reporter" and (self.is_admin or self.is_superadmin)

    def _get_session_auth_hash(self, secret=None):
        return salted_hmac(
            "cbng_reporter.models.User.session_auth_hash",
            f"{self.pk}:{self.username}",
            secret=secret,
            algorithm="sha256",
        ).hexdigest()

    def delete(self, *args, **kwargs):
        with transaction.atomic():
            Comment.objects.filter(user_id=self.id).update(user_id=ANONYMOUS_USER_ID)
            Report.objects.filter(reporter_id=self.id).update(reporter_id=ANONYMOUS_USER_ID)
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM `users` WHERE `userid` = %s", [self.id])


class Report(models.Model):
    vandalism = models.OneToOneField(
        Vandalism, primary_key=True, db_column="revertid", on_delete=models.DO_NOTHING, related_name="report"
    )
    timestamp = models.DateTimeField(db_default=Now())
    reporter_id = models.IntegerField(db_column="reporterid", db_index=True)
    reporter = models.CharField(max_length=128)
    status = models.IntegerField(choices=ReportStatus.choices, db_index=True)

    class Meta:
        db_table = "reports"

    @property
    def is_anonymous(self) -> bool:
        return self.reporter_id == ANONYMOUS_USER_ID


class Comment(models.Model):
    id = models.AutoField(primary_key=True, db_column="commentid")
    report = models.ForeignKey(
        Report, db_column="revertid", db_constraint=False, on_delete=models.DO_NOTHING, related_name="comments"
    )
    timestamp = models.DateTimeField(db_default=Now())
    user_id = models.IntegerField(db_column="userid", db_index=True)
    username = models.CharField(max_length=128, db_column="user")
    comment = models.TextField()

    class Meta:
        db_table = "comments"
        ordering: ClassVar = ["id"]

    @property
    def is_anonymous(self) -> bool:
        return self.user_id == ANONYMOUS_USER_ID


class EditSentForReview(models.Model):
    """Tracks which user sent a report to the review interface"""

    pk = models.CompositePrimaryKey("vandalism_id", "user_id")
    vandalism = models.ForeignKey(Vandalism, db_column="revertid", on_delete=models.DO_NOTHING)
    user_id = models.IntegerField(db_column="userid")

    class Meta:
        db_table = "edits_sent_for_review"
