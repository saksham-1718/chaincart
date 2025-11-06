"""
Django settings for backend project.
"""

from pathlib import Path
import os
from dotenv import load_dotenv

# ======================================
# Load environment variables
# ======================================
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# ======================================
# Basic Django Settings
# ======================================
SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-placeholder")
DEBUG = False
ALLOWED_HOSTS = ['.vercel.app', 'localhost']
# ======================================
# Application Definition
# ======================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'backend.wsgi.application'

# ======================================
# Databases
# ======================================
# Default Django DB (only for admin/auth)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ======================================
# MongoDB Configuration (used by core/mongo.py)
# ======================================
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://sakshamsingh171845_db_user:Saksham1718@cluster0.6vepxmg.mongodb.net/?appName=Cluster0")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "chaincart")

# ======================================
# Razorpay & Blockchain Config
# ======================================
# RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
# RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")

# WEB3_RPC_URL = os.getenv("WEB3_RPC_URL")
# PRIVATE_KEY = os.getenv("PRIVATE_KEY")
# CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
# CHAIN_ID = int(os.getenv("CHAIN_ID", "80001"))  # Default to Mumbai testnet

# ======================================
# Static and Media Files
# ======================================
STATIC_URL = '/static/'
STATICFILES_DIRS = (os.path.join(BASE_DIR, "static"),)

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ======================================
# Authentication
# ======================================
LOGIN_URL = '/login/'

# ======================================
# Default Primary Key Field Type
# ======================================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = (os.path.join(BASE_DIR, "static"),)
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'



# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'



MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

LOGIN_URL = '/login/'
