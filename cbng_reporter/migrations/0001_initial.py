import django.db.models.deletion
import django.db.models.functions.datetime
from django.db import migrations, models

# The tables pre-date this application, this is the exact schema from the legacy report interface
# (resources/database.sql), so the database operations are a no-op where the tables already exist.
LEGACY_SCHEMA = [
    """
    CREATE TABLE IF NOT EXISTS `reports` (
        `revertid` int(11) NOT NULL,
        `timestamp` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
        `reporterid` int(11) NOT NULL,
        `reporter` varchar(128) NOT NULL,
        `status` int(11) NOT NULL,
        PRIMARY KEY (`revertid`),
        KEY `reporterid` (`reporterid`),
        KEY `status` (`status`),
        CONSTRAINT `reports_ibfk_1` FOREIGN KEY (`revertid`) REFERENCES `vandalism` (`id`) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci
    """,
    """
    CREATE TABLE IF NOT EXISTS `comments` (
        `commentid` int(11) NOT NULL AUTO_INCREMENT,
        `revertid` int(11) NOT NULL,
        `timestamp` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
        `userid` int(11) NOT NULL,
        `user` varchar(128) NOT NULL,
        `comment` text NOT NULL,
        PRIMARY KEY (`commentid`),
        KEY `revertid` (`revertid`),
        KEY `userid` (`userid`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci
    """,
    """
    CREATE TABLE IF NOT EXISTS `users` (
        `userid` int(11) NOT NULL AUTO_INCREMENT,
        `username` varchar(128) NOT NULL,
        `admin` tinyint(1) NOT NULL DEFAULT 0,
        `superadmin` tinyint(1) NOT NULL DEFAULT 0,
        `next_on_review` tinyint(1) DEFAULT 1,
        `keyboard_shortcuts` tinyint(1) DEFAULT 1,
        `hide_anon` tinyint(1) DEFAULT 0,
        PRIMARY KEY (`userid`),
        UNIQUE KEY `username` (`username`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci
    """,
    """
    CREATE TABLE IF NOT EXISTS `edits_sent_for_review` (
        `revertid` int(11) NOT NULL,
        `userid` int(11) NOT NULL,
        PRIMARY KEY (`revertid`, `userid`),
        CONSTRAINT `reports_ibfk_2` FOREIGN KEY (`revertid`) REFERENCES `vandalism` (`id`) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci
    """,
]


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Beaten",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("timestamp", models.DateTimeField(db_default=django.db.models.functions.datetime.Now())),
                ("article", models.CharField(max_length=256)),
                ("diff", models.CharField(max_length=512)),
                ("user", models.CharField(max_length=256)),
            ],
            options={
                "db_table": "beaten",
                "abstract": False,
                "managed": False,
            },
        ),
        migrations.CreateModel(
            name="Vandalism",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("timestamp", models.DateTimeField(db_default=django.db.models.functions.datetime.Now())),
                ("user", models.CharField(max_length=256)),
                ("article", models.CharField(max_length=256)),
                ("heuristic", models.CharField(max_length=64)),
                ("regex", models.CharField(max_length=2048, null=True)),
                ("reason", models.CharField(max_length=512)),
                ("diff", models.CharField(max_length=512)),
                ("old_id", models.IntegerField()),
                ("new_id", models.IntegerField()),
                ("reverted", models.BooleanField()),
            ],
            options={
                "db_table": "vandalism",
                "abstract": False,
                "managed": False,
            },
        ),
        # Note: Never drop the tables on reverse
        migrations.SeparateDatabaseAndState(
            database_operations=[migrations.RunSQL(sql, reverse_sql=migrations.RunSQL.noop) for sql in LEGACY_SCHEMA],
            state_operations=[
                migrations.CreateModel(
                    name="User",
                    fields=[
                        ("id", models.AutoField(db_column="userid", primary_key=True, serialize=False)),
                        ("username", models.CharField(max_length=128, unique=True)),
                        ("is_admin", models.BooleanField(db_column="admin", default=False)),
                        ("is_superadmin", models.BooleanField(db_column="superadmin", default=False)),
                        ("next_on_review", models.BooleanField(default=True, null=True)),
                        ("keyboard_shortcuts", models.BooleanField(default=True, null=True)),
                        ("hide_anon", models.BooleanField(default=False, null=True)),
                    ],
                    options={
                        "db_table": "users",
                    },
                ),
                migrations.CreateModel(
                    name="Report",
                    fields=[
                        (
                            "vandalism",
                            models.OneToOneField(
                                db_column="revertid",
                                on_delete=django.db.models.deletion.DO_NOTHING,
                                primary_key=True,
                                related_name="report",
                                serialize=False,
                                to="cbng_reporter.vandalism",
                            ),
                        ),
                        ("timestamp", models.DateTimeField(db_default=django.db.models.functions.datetime.Now())),
                        ("reporter_id", models.IntegerField(db_column="reporterid", db_index=True)),
                        ("reporter", models.CharField(max_length=128)),
                        (
                            "status",
                            models.IntegerField(
                                choices=[
                                    (0, "Reported"),
                                    (1, "Invalid"),
                                    (2, "Sending to Review Interface"),
                                    (3, "Bug"),
                                    (4, "Resolved"),
                                    (5, "Queued to be reviewed"),
                                    (6, "Partially reviewed"),
                                    (7, "Reviewed - Included in dataset as Constructive"),
                                    (8, "Reviewed - Included in dataset as Vandalism"),
                                    (9, "Reviewed - Not included in dataset"),
                                    (10, "Edit Data Has Been Removed"),
                                ],
                                db_index=True,
                            ),
                        ),
                    ],
                    options={
                        "db_table": "reports",
                    },
                ),
                migrations.CreateModel(
                    name="EditSentForReview",
                    fields=[
                        (
                            "pk",
                            models.CompositePrimaryKey(
                                "vandalism_id", "user_id", blank=True, editable=False, primary_key=True, serialize=False
                            ),
                        ),
                        ("user_id", models.IntegerField(db_column="userid")),
                        (
                            "vandalism",
                            models.ForeignKey(
                                db_column="revertid",
                                on_delete=django.db.models.deletion.DO_NOTHING,
                                to="cbng_reporter.vandalism",
                            ),
                        ),
                    ],
                    options={
                        "db_table": "edits_sent_for_review",
                    },
                ),
                migrations.CreateModel(
                    name="Comment",
                    fields=[
                        ("id", models.AutoField(db_column="commentid", primary_key=True, serialize=False)),
                        ("timestamp", models.DateTimeField(db_default=django.db.models.functions.datetime.Now())),
                        ("user_id", models.IntegerField(db_column="userid", db_index=True)),
                        ("username", models.CharField(db_column="user", max_length=128)),
                        ("comment", models.TextField()),
                        (
                            "report",
                            models.ForeignKey(
                                db_column="revertid",
                                db_constraint=False,
                                on_delete=django.db.models.deletion.DO_NOTHING,
                                related_name="comments",
                                to="cbng_reporter.report",
                            ),
                        ),
                    ],
                    options={
                        "db_table": "comments",
                        "ordering": ["id"],
                    },
                ),
            ],
        ),
    ]
