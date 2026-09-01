"""
Django settings for the RMW project (Rit-Match-Werkbon).

Settings that differ per environment are read from environment variables, so the
same image can run locally and on the server without code changes. Defaults are
development-friendly; production values come from the environment (see
.env.example).

Docs: https://docs.djangoproject.com/en/5.2/ref/settings/
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name: str, default: bool = False) -> bool:
    """Read a boolean from the environment ("1", "true", "yes" are truthy)."""
    return os.environ.get(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: str = "") -> list[str]:
    """Read a comma-separated list from the environment."""
    return [item.strip() for item in os.environ.get(name, default).split(",") if item.strip()]


# SECURITY WARNING: keep the secret key used in production secret.
# The fallback is for local development only; production must set RMW_SECRET_KEY.
SECRET_KEY = os.environ.get(
    "RMW_SECRET_KEY",
    "django-insecure-dev-only-key-change-me-in-any-real-deployment",
)

# SECURITY WARNING: never run with debug turned on in production.
DEBUG = env_bool("RMW_DEBUG", True)

ALLOWED_HOSTS = env_list("RMW_ALLOWED_HOSTS", "localhost,127.0.0.1,[::1]")

# Needed when the app is served behind a proxy/hostname other than localhost.
CSRF_TRUSTED_ORIGINS = env_list("RMW_CSRF_TRUSTED_ORIGINS")


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "matching",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "rmw.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
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

WSGI_APPLICATION = "rmw.wsgi.application"


# Database
# SQLite for development. The production database has not been chosen yet
# (out of scope for roadmap phase 1); RMW_DB_PATH lets the container point the
# SQLite file at a mounted volume so data survives a container rebuild.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": Path(os.environ.get("RMW_DB_PATH", BASE_DIR / "db.sqlite3")),
    }
}


# Password validation

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Internationalization
# UI language is Dutch (project convention); the customer works in Dutch time.
LANGUAGE_CODE = "nl-nl"

TIME_ZONE = "Europe/Amsterdam"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, images)

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# RMW-specific settings
# Directory that the app watches for the daily Syntess exports and the
# RouteVision download. On the server this is a mount of the share
# \\stroes-1909\atrium\Autoprint\RUUDS (see docs/architecture.md). Nothing reads
# this yet — file ingestion is roadmap phase 2.
RMW_INBOX_DIR = Path(os.environ.get("RMW_INBOX_DIR", BASE_DIR / "data" / "inbox"))


# Logging: plain console output, which is what a container should emit.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {"format": "{asctime} {levelname} {name}: {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "simple"},
    },
    "root": {"handlers": ["console"], "level": os.environ.get("RMW_LOG_LEVEL", "INFO")},
}
