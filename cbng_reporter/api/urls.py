from django.urls import path

from cbng_reporter.api import views

urlpatterns = [
    path("v1/review/export/", views.review_export, name="api-review-export"),
    path("v1/review/export/users/", views.review_export_users, name="api-review-export-users"),
    path("v1/statistics/", views.statistics, name="api-statistics"),
]
