import sys
from pathlib import Path

import prometheus_client

from cbng_reporter.utils.config import detect_if_running_in_test, load_config

BASE_DIR = Path(__file__).resolve().parent.parent
IN_TEST = detect_if_running_in_test()
CONFIG = load_config(BASE_DIR, IN_TEST)

SECRET_KEY = CONFIG["django"]["secret_key"]
DEBUG = CONFIG["django"]["debug"]

ALLOWED_HOSTS = ["*"]
CSRF_TRUSTED_ORIGINS = ["https://cluebotng.toolforge.org"]

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.messages",
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles",
    "django_prometheus",
    "django_bootstrap5",
    "cbng_reporter",
]

MIDDLEWARE = [
    "django_prometheus.middleware.PrometheusBeforeMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_prometheus.middleware.PrometheusAfterMiddleware",
]

ROOT_URLCONF = "cbng_reporter.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "cbng_reporter.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django_prometheus.db.backends.mysql",
        "NAME": CONFIG["mysql"]["default"]["schema"],
        "HOST": CONFIG["mysql"]["default"]["host"],
        "PORT": CONFIG["mysql"]["default"]["port"],
        "USER": CONFIG["mysql"]["default"]["user"],
        "PASSWORD": CONFIG["mysql"]["default"]["password"],
        "OPTIONS": {
            "charset": "utf8mb4",
            "ssl_mode": "DISABLED",
            "init_command": "SET time_zone = '+00:00'",
        },
    },
}

DATABASE_ROUTERS = ["cbng_reporter.libs.database.DatabaseRouter"]

REDIS_HOST = CONFIG["redis"]["host"]
REDIS_PORT = CONFIG["redis"]["port"]
REDIS_DB = CONFIG["redis"]["db"]
REDIS_PASSWORD = CONFIG["redis"]["password"]

CACHES = {
    "default": (
        {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}
        if IN_TEST or not REDIS_HOST
        else {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": (
                f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
                if REDIS_PASSWORD
                else f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
            ),
            "KEY_PREFIX": "cbng_reporter",
        }
    )
}

SESSION_ENGINE = "django.contrib.sessions.backends.cache"
MESSAGE_STORAGE = "django.contrib.messages.storage.cookie.CookieStorage"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "%(asctime)s %(levelname)s %(filename)s %(funcName)s: %(message)s"},
        "message_only": {"format": "%(message)s"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "console_message": {
            "class": "logging.StreamHandler",
            "formatter": "message_only",
        },
    },
    "loggers": {
        "": {"handlers": ["console"], "level": "INFO", "propagate": True, "stream": sys.stdout},
        "cbng_reporter.access_log": {"handlers": ["console_message"], "level": "INFO", "propagate": False},
    },
}

AUTH_USER_MODEL = "cbng_reporter.User"

BOOTSTRAP5 = {
    "css_url": {
        "url": "https://tools-static.wmflabs.org/cdnjs/ajax/libs/bootstrap/5.3.7/css/bootstrap.min.css",
        "crossorigin": "anonymous",
    },
    "javascript_url": {
        "url": "https://tools-static.wmflabs.org/cdnjs/ajax/libs/bootstrap/5.3.7/js/bootstrap.bundle.min.js",
        "crossorigin": "anonymous",
    },
}

LANGUAGE_CODE = "en-gb"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "static"
STORAGES = {
    "staticfiles": {
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
            if IN_TEST
            else "whitenoise.storage.CompressedManifestStaticFilesStorage"
        ),
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

REVIEWER_URL = CONFIG["reviewer"]["url"]
CBNG_REPORTS_PER_PAGE = 50

PROMETHEUS_METRIC_NAMESPACE = "cbng_reporter"
prometheus_client.REGISTRY.unregister(prometheus_client.GC_COLLECTOR)
prometheus_client.REGISTRY.unregister(prometheus_client.PLATFORM_COLLECTOR)
prometheus_client.REGISTRY.unregister(prometheus_client.PROCESS_COLLECTOR)
