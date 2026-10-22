from django.test import SimpleTestCase

from cbng_reporter.libs.wikipedia import WikipediaReader


class WikipediaReaderTestCase(SimpleTestCase):
    def testGetUserRights(self):
        rights = WikipediaReader().get_user_rights("ClueBot NG")
        self.assertIn("edit", rights)

    def testGetDiff(self):
        diff = WikipediaReader().get_diff(1381243114)
        self.assertIn("diff-lineno", diff.html)
        self.assertEqual((diff.old.id, diff.new.id), (1381199850, 1381243114))
        self.assertEqual(diff.new.user, "~2026-56189-31")
