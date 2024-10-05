"""
Django settings for versel_deploymet project.

Generated by 'django-admin startproject' using Django 4.1.3.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""
import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-=cldztbc4jg&xl0!x673!*v2_=p$$eu)=7*f#d0#zs$44xx-h^'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', '.vercel.app', '.now.sh', '127.0.0.1:8080', '127.0.0.1:8081']

CORS_ORIGIN_ALLOW_ALL = True
# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'drf_yasg',
    'rest_framework.authtoken',

    'cloudinary_storage',
    'cloudinary',
    'example'
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    # 'example.middlewares.DisableCSRFMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'versel_deploymet.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'versel_deploymet.wsgi.app'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
}
        # 'rest_framework.authentication.SessionAuthentication'
# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases
# Note: Django modules for using databases are not support in serverless
# environments like Vercel. You can use a database over HTTP, hosted elsewhere.

DATABASES = {
    # "default": {
    #     "ENGINE": "django.db.backends.sqlite3",
    #     "NAME": BASE_DIR / "db.sqlite3",
    # }

#     POSTGRES_URL="postgres://default:nq4X8BGTDKCu@ep-restless-cloud-a4msixdi-pooler.us-east-1.aws.neon.tech:5432/verceldb?sslmode=require"
# POSTGRES_PRISMA_URL="postgres://default:nq4X8BGTDKCu@ep-restless-cloud-a4msixdi-pooler.us-east-1.aws.neon.tech:5432/verceldb?sslmode=require&pgbouncer=true&connect_timeout=15"
# POSTGRES_URL_NO_SSL="postgres://default:nq4X8BGTDKCu@ep-restless-cloud-a4msixdi-pooler.us-east-1.aws.neon.tech:5432/verceldb"
# POSTGRES_URL_NON_POOLING="postgres://default:nq4X8BGTDKCu@ep-restless-cloud-a4msixdi.us-east-1.aws.neon.tech:5432/verceldb?sslmode=require"
# POSTGRES_USER="default"
# POSTGRES_HOST="ep-restless-cloud-a4msixdi-pooler.us-east-1.aws.neon.tech"
# POSTGRES_PASSWORD="nq4X8BGTDKCu"
# POSTGRES_DATABASE="verceldb"

    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'verceldb',
        'USER': 'default',
        'PASSWORD': 'nq4X8BGTDKCu',
        'HOST': 'ep-restless-cloud-a4msixdi-pooler.us-east-1.aws.neon.tech',
        'PORT': '5432',  # Assuming default PostgreSQL port
        'OPTIONS': {
            'sslmode': 'require',  # Ensures that SSL is used
            'options': 'endpoint=ep-restless-cloud-a4msixdi-pooler'
        },
    }
}

SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {'api_key': {'type': 'apiKey', 'in': 'header', 'name': 'Authorization'}},
    'REFETCH_SCHEMA_WITH_AUTH': False,
}
# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

import os

STATIC_URL = 'static/'
STATICFILES_DIRS = os.path.join(BASE_DIR, 'static'),
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles_build', 'static')

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = "example.User"  # updated
AUTHENTICATION_BACKENDS = ["example.backends.EmailBackend"]  # updated

CLOUDINARY_STORAGE = {
    'CLOUD_NAME': 'dcqeugna3',
    'API_KEY': '424258596713575',
    'API_SECRET': 'podU121kbELuOEEDob9w3rLQg0w'
}
MEDIA_URL = '/media/'  # or any prefix you choose
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage' 
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_USE_TLS = True
EMAIL_PORT = 587
EMAIL_HOST_USER = 'krystal@ibexbuilderstudios.com'
EMAIL_HOST_PASSWORD = 'fokc ocot bmdu vgme'


FRONTEND_BASE_URL = 'https://ibexbuildersstudio.netlify.app/'



PAYPAL_ID = 'AQdIN4BuFzhRSikJGrdSFgfy8jckkiGdBMYJnri2CH3Kq0sJuefkmYHnt7EBFp4nPTEWefw1cr9neZ8P'

PAYPAL_SECRET= 'EODq3hVDjOAa69SQea5bLvNd_Wsh_YlBcTX6LKJtOmm3IMpcDpnRA4VCL85tha6PcGtCbfiYxmQyqEmI'
PAYPAL_BASE_URL='https://api.sandbox.paypal.com'


