from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from cbng_reporter.constants import MANAGE_USERS_PERMISSION
from cbng_reporter.models import User

USER_FLAG_ACTIONS = {
    "superadmin": {"is_superadmin": True},
    "admin": {"is_admin": True},
    "deadmin": {"is_admin": False},
}

USER_ACTIONS = [
    ("delete", "X", "Delete user"),
    ("superadmin", "++", "Grant super admin"),
    ("admin", "+", "Grant admin"),
    ("deadmin", "-", "Remove admin"),
]


@login_required
@permission_required(MANAGE_USERS_PERMISSION, raise_exception=True)
def users(request):
    return render(
        request, "cbng_reporter/admin/users.html", {"users": User.objects.order_by("id"), "user_actions": USER_ACTIONS}
    )


@require_POST
@login_required
@permission_required(MANAGE_USERS_PERMISSION, raise_exception=True)
def user_action(request, id: int, action: str):
    user = get_object_or_404(User, id=id)

    if user.is_superadmin:
        messages.error(request, f"{user.username} is a super admin and cannot be modified.")
        return redirect("admin-users")

    if action == "delete":
        user.delete()
        messages.success(request, f"Deleted {user.username}.")

    elif flags := USER_FLAG_ACTIONS.get(action):
        for field, value in flags.items():
            setattr(user, field, value)
        user.save(update_fields=list(flags.keys()))
        messages.success(request, f"Updated {user.username}.")

    else:
        return HttpResponseBadRequest("Unknown action")

    return redirect("admin-users")
