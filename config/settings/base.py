from pathlib import Path

from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
# BASE_DIR is sitadc-youth-hub (3 levels up from base.py: base.py -> settings -> config -> root)  # noqa: E501
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load environment variables from .env file
load_dotenv(BASE_DIR / ".env")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "apps.core.apps.CoreConfig",
    "apps.accounts.apps.AccountsConfig",
    "apps.leadership.apps.LeadershipConfig",
    "apps.volunteers.apps.VolunteersConfig",
    "apps.memberships.apps.MembershipsConfig",
    "apps.stakeholders.apps.StakeholdersConfig",
    "apps.programs.apps.ProgramsConfig",
    "apps.beneficiaries.apps.BeneficiariesConfig",
    "apps.meal.apps.MealConfig",
    "apps.reports.apps.ReportsConfig",
    "apps.report_instances.apps.ReportInstancesConfig",
    "apps.reviews.apps.ReviewsConfig",
    "apps.documents.apps.DocumentsConfig",
    "apps.registers.apps.RegistersConfig",
    "apps.meetings.apps.MeetingsConfig",
    "apps.notifications.apps.NotificationsConfig",
    "apps.search.apps.SearchConfig",
    "apps.exports.apps.ExportsConfig",
    "apps.governance.apps.GovernanceConfig",
    "apps.communications.apps.CommunicationsConfig",
    "apps.rbac.apps.RbacConfig",
    "apps.references.apps.ReferencesConfig",
    "apps.system_settings.apps.SystemSettingsConfig",
    "apps.settings.apps.SettingsConfig",
    "apps.finance.apps.FinanceConfig",
    "apps.organizations.apps.OrganizationsConfig",
    "apps.dashboard.apps.DashboardConfig",
]

MIDDLEWARE = [
    "apps.core.middleware.RequestIDMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "apps.core.middleware.SecurityHeadersMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "apps.rbac.middleware.AuthorizationMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.branding_context",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Lusaka"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"
PRIVATE_MEDIA_ROOT = BASE_DIR / "private_media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Logging Configuration
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "apps": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
    }
}

# Authentication Settings
AUTH_USER_MODEL = "accounts.User"
LOGIN_URL = "core:login"
LOGIN_REDIRECT_URL = "dashboard:home"
LOGOUT_REDIRECT_URL = "core:login"

# Session Cookie and Inactivity configurations
SESSION_COOKIE_AGE = 1209600  # 2 weeks in seconds
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_TIMEOUT_SECONDS = 900  # 15 minutes
SESSION_ACTIVITY_UPDATE_INTERVAL_SECONDS = 60