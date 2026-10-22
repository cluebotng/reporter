import logging

from django.conf import settings
from social_core.exceptions import AuthPolicyError

from cbng_reporter.libs.auth.rights import AutoAdminRightsChecker
from cbng_reporter.libs.models import SocialLogin
from cbng_reporter.models import User

logger = logging.getLogger(__name__)


def reject_blocked_users(backend, details, *args, **kwargs):
    if backend.name == settings.SOCIAL_AUTH_BACKEND_NAME and details.get("blocked"):
        logger.info(f"Rejecting login from blocked user {details.get('username')}")
        raise AuthPolicyError(backend, code="authentication_disallowed", stage="pipeline")


def get_or_create_user(backend, details, uid, *args, **kwargs):
    user, created = User.objects.get_or_create(username=details["username"])
    if created:
        logger.info(f"Created user {user.username} ({user.id})")
    return {"user": user, "is_new": created, "social": SocialLogin(provider=backend.name, uid=f"{uid}")}


def check_for_auto_admin_rights(backend, user, *args, **kwargs):
    if backend.name == settings.SOCIAL_AUTH_BACKEND_NAME:
        AutoAdminRightsChecker().execute(user)
