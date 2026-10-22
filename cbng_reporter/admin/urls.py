from django.urls import path

from cbng_reporter.admin import views

urlpatterns = [
    path("users/", views.users, name="admin-users"),
    path("users/<int:id>/<str:action>/", views.user_action, name="admin-user-action"),
]
