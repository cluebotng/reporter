"""
Mapping of the legacy (PHP) url structure to the current urls, so existing links keep working.

Pages were `/?page=<name>&...` (or `/index.php?page=...`).
"""

from urllib.parse import urlencode

from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseNotFound,
    HttpResponsePermanentRedirect,
)
from django.urls import reverse


def _int_or_none(value: str | None) -> int | None:
    try:
        return int(value)
    except TypeError, ValueError:
        return None


def _redirect(request: HttpRequest, url: str, params: dict | None = None) -> HttpResponse:
    if params := {k: v for k, v in (params or {}).items() if v is not None}:
        url = f"{url}?{urlencode(params)}"

    return HttpResponsePermanentRedirect(url, preserve_request=(request.method == "POST"))


def _redirect_list(request: HttpRequest, args) -> HttpResponse:
    idx = _int_or_none(args.get("idx")) or 0
    return _redirect(
        request,
        reverse("report-list"),
        {"page": idx + 1 if idx > 0 else None, "show_all": "1" if "showall" in args else None},
    )


def _redirect_view(request: HttpRequest, args) -> HttpResponse:
    if revert_id := _int_or_none(args.get("id")):
        return _redirect(request, reverse("report-view", kwargs={"id": revert_id}))
    if new_id := _int_or_none(args.get("new_id")):
        return _redirect(request, reverse("report-by-revision", kwargs={"new_id": new_id}))
    return _redirect(request, reverse("report-list"))


def _redirect_report(request: HttpRequest, args) -> HttpResponse:
    if revert_id := _int_or_none(args.get("id")):
        return _redirect(request, reverse("report", kwargs={"id": revert_id}))
    return _redirect(request, reverse("home"))


LEGACY_PAGES = {
    "Main": lambda request, args: _redirect(request, reverse("home")),
    "List": _redirect_list,
    "View": _redirect_view,
    "Report": _redirect_report,
    "Sign In": lambda request, args: _redirect(request, reverse("login")),
    "Sign Out": lambda request, args: _redirect(request, reverse("report-list")),
    "Options": lambda request, args: _redirect(request, reverse("options")),
    "User Admin": lambda request, args: _redirect(request, reverse("admin-users")),
}


def legacy_page_redirect(request: HttpRequest) -> HttpResponse | None:
    if "page" not in request.GET:
        return None

    if handler := LEGACY_PAGES.get(request.GET["page"]):
        return handler(request, request.GET)
    return HttpResponseNotFound("404 - File not found.", content_type="text/plain")
