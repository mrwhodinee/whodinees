"""
Django settings for Whodinees e-commerce.
"""
from pathlib import Path
import os
import environ
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent  # whodinees/ (the repo root)

env = environ.Env(
    DEBUG=(bool, False),
)

# Load .env file from backend/ if present (gitignored)
env_file = BASE_DIR / ".env"
if env_file.exists():
    environ.Env.read_env(str(env_file))

SECRET_KEY = env("DJANGO_SECRET_KEY", default="dev-insecure-change-me-please-xxxx")
DEBUG = env.bool("DEBUG", default=False)

ALLOWED_HOSTS = [
    "whodinees.com",
    "www.whodinees.com",
    "whodinees.herokuapp.com",
    "whodinees-8802a535baa6.herokuapp.com",
    "localhost",
    "127.0.0.1",
    ".herokuapp.com",  # permissive for the default app domain
]
if DEBUG:
    ALLOWED_HOSTS.append("testserver")

# Trusted origins for CSRF on HTTPS hosts
CSRF_TRUSTED_ORIGINS = [
    "https://whodinees.com",
    "https://www.whodinees.com",
    "https://whodinees.herokuapp.com",
    "https://whodinees-8802a535baa6.herokuapp.com",
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "store",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "whodinees.urls"

# Where the React build goes after heroku-postbuild / local build.
# Whitenoise will serve /assets/ etc. from STATIC_ROOT; the catch-all view
# returns index.html from this directory.
FRONTEND_DIST_DIR = PROJECT_ROOT / "frontend" / "dist"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "templates",
            FRONTEND_DIST_DIR,
        ],
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

WSGI_APPLICATION = "whodinees.wsgi.application"

# Database: DATABASE_URL in prod (Heroku Postgres), SQLite fallback locally.
DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
        ssl_require=env.bool("DB_SSL_REQUIRE", default=False),
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
# Additional source directories for collectstatic to hoover up
STATICFILES_DIRS = []
# The React build dir (if it exists) is served as a static source
if FRONTEND_DIST_DIR.exists():
    STATICFILES_DIRS.append(FRONTEND_DIST_DIR)

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

# Media (uploaded product images / Meshy downloads)
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# DRF
REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
}

# CORS — in dev, allow localhost frontends
CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS",
    default=["http://localhost:5173", "http://127.0.0.1:5173"],
)
CORS_ALLOW_CREDENTIALS = True

# ---- Third-party service keys (read from env) ----
STRIPE_PUBLISHABLE_KEY = env("STRIPE_PUBLISHABLE_KEY", default="")
STRIPE_SECRET_KEY = env("STRIPE_SECRET_KEY", default="")
STRIPE_WEBHOOK_SECRET = env("STRIPE_WEBHOOK_SECRET", default="")

MESHY_API_KEY = env("MESHY_API_KEY", default="")

SHAPEWAYS_CLIENT_ID = env("SHAPEWAYS_CLIENT_ID", default="")
SHAPEWAYS_CLIENT_SECRET = env("SHAPEWAYS_CLIENT_SECRET", default="")
SHAPEWAYS_CONSUMER_KEY = env("SHAPEWAYS_CONSUMER_KEY", default="")
SHAPEWAYS_CONSUMER_SECRET = env("SHAPEWAYS_CONSUMER_SECRET", default="")

SENDGRID_API_KEY = env("SENDGRID_API_KEY", default="")
SENDGRID_FROM_EMAIL = env("SENDGRID_FROM_EMAIL", default="orders@whodinees.com")

ANTHROPIC_API_KEY = env("ANTHROPIC_API_KEY", default="")
BRAVE_API_KEY = env("BRAVE_API_KEY", default="")

# Security (prod-ish; only bite when DEBUG=False and behind Heroku router)
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 60 * 60 * 24  # 1 day; increase later
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_CONTENT_TYPE_NOSNIFF = True

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "store": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}
