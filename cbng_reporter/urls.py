from django.http import HttpResponse
from django.urls import path

urlpatterns = [
    # For developers
    path("internal/health/", lambda r: HttpResponse("OK")),
]
