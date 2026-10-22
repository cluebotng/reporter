from django.http import HttpResponse
from django.urls import include, path
from django.views.decorators.http import require_GET
from social_django import views as social_views

from cbng_reporter import views

urlpatterns = [
    # For developers
    path("internal/health/", lambda r: HttpResponse("OK")),
    path("internal/metrics/", views.metrics),
    # Authentication
    path(
        "oauth/",
        include(
            (
                [
                    path("login/<str:backend>/", social_views.auth, name="begin"),
                    path("complete/<str:backend>/", require_GET(social_views.complete), name="complete"),
                ],
                "social",
            )
        ),
    ),
    path("login/", views.login, name="login"),
    path("logout/", views.logout, name="logout"),
    # Admin
    path("admin/", include("cbng_reporter.admin.urls")),
    # Reporting
    path("report/", views.report_lookup, name="report-lookup"),
    path("report/<int:id>/", views.report, name="report"),
    # Reports
    path("reports/", views.report_list, name="report-list"),
    path("reports/by-revision/<int:new_id>/", views.report_by_revision, name="report-by-revision"),
    path("reports/<int:id>/", views.report_view, name="report-view"),
    path("reports/<int:id>/comment/", views.report_comment, name="report-comment"),
    path("reports/<int:id>/status/", views.report_status, name="report-status"),
    path(
        "reports/<int:id>/comments/<int:comment_id>/delete/",
        views.report_comment_delete,
        name="report-comment-delete",
    ),
    # User
    path("options/", views.options, name="options"),
    # Public
    path("index.php", views.home),
    path("", views.home, name="home"),
]
