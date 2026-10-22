import logging
import time
from datetime import UTC, datetime

from django.http import HttpRequest

logger = logging.getLogger(__name__)


class AuthenticatedRequestLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self._logger = logging.getLogger("cbng_reporter.access_log")

    def __call__(self, request: HttpRequest):
        processing_start = time.monotonic()
        response = self.get_response(request)
        processing_finish = time.monotonic()

        if request.user.is_authenticated:
            self._logger.info(
                '%s [%s] "%s %s" %d %s "%s" "%s" %dms',
                request.user.get_username(),
                datetime.now(UTC).strftime("%d/%b/%Y:%H:%M:%S +0000"),
                request.method,
                request.get_full_path(),
                response.status_code,
                response.get("Content-Length", "-"),
                request.META.get("HTTP_REFERER", "-"),
                request.META.get("HTTP_USER_AGENT", "-"),
                int((processing_finish - processing_start) * 1000),
            )

        return response
