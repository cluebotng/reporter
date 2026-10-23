from django.test import TestCase, override_settings


class MetricsTestCase(TestCase):
    def testMetricsWithoutSharedSecret(self):
        self.assertEqual(self.client.get("/internal/metrics/").status_code, 200)

    @override_settings(MONITORING_SHARED_SECRET="very secret")
    def testMetricsWithSharedSecret(self):
        self.assertEqual(self.client.get("/internal/metrics/").status_code, 403)
        self.assertEqual(
            self.client.get("/internal/metrics/", headers={"Authorization": "Bearer wrong"}).status_code, 403
        )
        self.assertEqual(
            self.client.get("/internal/metrics/", headers={"Authorization": "Bearer very secret"}).status_code, 200
        )
