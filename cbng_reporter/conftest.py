import pathlib
from unittest import mock

import pytest
from django.db import connections
from django.db.models.signals import pre_migrate
from django.dispatch import receiver

SCHEMA_FILE = pathlib.PosixPath(__file__).parent / "tests" / "data" / "schema.sql"
_schema_loaded_for = set()


@receiver(pre_migrate)
def create_external_tables(using, **kwargs):
    if using in _schema_loaded_for:
        return

    with SCHEMA_FILE.open("r") as fh:
        statements = [statement.strip() for statement in fh.read().split(";\n") if statement.strip()]

    with connections[using].cursor() as cursor:
        for statement in statements:
            cursor.execute(statement)
    _schema_loaded_for.add(using)


def pytest_collection_modifyitems(config, items):
    test_dir = pathlib.PosixPath(__file__).parent / "tests"
    package_tags = {
        test_dir / "integration": pytest.mark.integration,
    }

    for item in items:
        test_path = pathlib.PosixPath(item.fspath)

        for package_dir, package_tag in package_tags.items():
            if test_path.is_relative_to(package_dir):
                item.add_marker(package_tag)

        if not any(item.iter_markers()):
            item.add_marker(pytest.mark.unmarked)


@pytest.fixture(autouse=True)
def mock_wikipedia(request):
    if request.node.get_closest_marker("integration"):
        yield None
        return

    with (
        mock.patch("cbng_reporter.libs.wikipedia.WikipediaReader.get_diff", return_value=None),
        mock.patch("cbng_reporter.libs.wikipedia.WikipediaReader.get_user_rights", return_value=set()) as rights,
    ):
        yield rights
