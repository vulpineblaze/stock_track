"""
Django settings for ycs_apps project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))




# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '1*bd%h5*$ypqmysa6b7=s4wp+@m*0(cl*_g)b_bgub-6k($4wj'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

TEMPLATE_DEBUG = False

# ALLOWED_HOSTS = []
# 

# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'ycs_apps.stock_track',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'ycs_apps.urls'

WSGI_APPLICATION = 'ycs_apps.wsgi.application'

ALLOWED_HOSTS = ("localhost",
                "127.0.0.1",
                "yourcompusolutions.com",
                "ycs2.yourcompusolutions.com")

# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

#~ DATABASES = {
    #~ 'default': {
        #~ 'ENGINE': 'django.db.backends.sqlite3',
        #~ 'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    #~ }
#~ }

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', 
        'NAME': 'stock_track_db',
        'USER': 'django',
        'PASSWORD': 'django',
        'HOST': 'localhost',   # Or an IP Address that your DB is hosted on
        'PORT': '3306',
    }
}

DATABASE_OPTIONS = {
    "connect_timeout": 6000,
}
# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'

STATIC_ROOT = os.path.join(BASE_DIR, '../staticfiles/')
