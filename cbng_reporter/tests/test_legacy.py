from django.test import TestCase


class LegacyPageRedirectTestCase(TestCase):
    def assertLegacyRedirect(self, url: str, expected: str, status_code: int = 301, **kwargs):
        r = self.client.get(url, **kwargs)
        self.assertEqual(r.status_code, status_code, url)
        self.assertEqual(r["Location"], expected, url)

    def testPages(self):
        for legacy_url, expected in [
            ("/?page=Main", "/"),
            ("/index.php?page=Main", "/"),
            ("/?page=List", "/reports/"),
            ("/?page=List&idx=0", "/reports/"),
            ("/?page=List&idx=2", "/reports/?page=3"),
            ("/?page=List&showall", "/reports/?show_all=1"),
            ("/?page=View&id=1234", "/reports/1234/"),
            ("/?page=View&id=1234&status=1", "/reports/1234/"),
            ("/?page=View&id=1234&deletecomment=5", "/reports/1234/"),
            ("/?page=View&new_id=5678", "/reports/by-revision/5678/"),
            ("/?page=View", "/reports/"),
            ("/?page=Report&id=1234", "/report/1234/"),
            ("/?page=Report", "/"),
            ("/?page=Sign+In", "/login/"),
            ("/?page=Sign+Out", "/reports/"),
            ("/?page=Options", "/options/"),
            ("/?page=User+Admin", "/admin/users/"),
        ]:
            self.assertLegacyRedirect(legacy_url, expected)

    def testUnknownPage(self):
        r = self.client.get("/?page=Nope")
        self.assertEqual(r.status_code, 404)

    def testReportSubmissionPreservesMethod(self):
        r = self.client.post("/?page=Report&id=1234", {"submit": "1", "comment": "Hello"})
        self.assertEqual(r.status_code, 308)
        self.assertEqual(r["Location"], "/report/1234/")
