import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

SECRET_KEY = '^d0!gm53217iw3jqr66svdtw$oc-$#5b+x7p)xc+5+m-ekvxf1'

DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'django_extensions',
    'rest_framework',

    'lab',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware', # tmp relax for lab.ajax.
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'mysite.urls'

WSGI_APPLICATION = 'mysite.wsgi.application'

db_path = os.path.join(BASE_DIR, '..', '..', 'lab_db', 'db.sqlite3')
# print 'db_path', db_path

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': db_path,
    },
}

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = False

STATIC_URL = '/static/'
statics = os.path.join(BASE_DIR, 'static')
# STATIC_ROOT = statics # useful for collectstatic.

TEMPLATE_DIRS = (
    os.path.join(BASE_DIR, 'templates'),
)

STATICFILES_DIRS = (
    statics,
)

REST_FRAMEWORK = {
    # 'PAGINATE_BY': 10
}

AUTH_USER_MODEL = 'lab.User'
