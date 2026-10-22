from django.core.management import call_command
from django.test import TestCase

from cbng_reporter.models import ReadOnlyTableError, Vandalism
from cbng_reporter.tests.utils import create_vandalism


class ModelsTestCase(TestCase):
    def testMigrationsMatchModels(self):
        call_command("makemigrations", "--check", "--dry-run", verbosity=0)

    def testBotTablesAreReadOnly(self):
        vandalism = create_vandalism()
        with self.assertRaises(ReadOnlyTableError):
            vandalism.save()
        with self.assertRaises(ReadOnlyTableError):
            Vandalism.objects.filter(id=vandalism.id).update(reason="")
