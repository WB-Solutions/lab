import os
from django.conf.global_settings import TEMPLATE_CONTEXT_PROCESSORS
from django.conf.global_settings import AUTHENTICATION_BACKENDS
import datetime

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

SECRET_KEY = '^d0!gm53217iw3jqr66svdtw$oc-$#5b+x7p)xc+5+m-ekvxf1'

DEBUG = True
TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []

# http://integricho.github.io/2013/07/22/mutant-introduction/
# https://github.com/integricho/mutant-sample-app
apps_mutant = (
    'south', # auto-installed by mutant.
    'mutant', # django-mutant
    'mutant.contrib.boolean',
    'mutant.contrib.temporal',
    'mutant.contrib.file',
    'mutant.contrib.numeric',
    'mutant.contrib.text',
    'mutant.contrib.web',
    'mutant.contrib.related',
    'mutantgui',
)
apps_mutant = () # DISABLED for now.

INSTALLED_APPS = (
    'suit', # django-suit

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'django_extensions', # django-extensions

) + apps_mutant + (

    'rest_framework', # djangorestframework
    # 'rest_framework.authtoken', # NOT in use, using JWT below (not required as installed app here) instead, http://www.django-rest-framework.org/api-guide/authentication.html#tokenauthentication
    # djangorestframework-jwt # https://github.com/GetBlimp/django-rest-framework-jwt

    'mptt', # django-mptt

    'allauth', # django-allauth
    'allauth.account',
    'allauth.socialaccount',
    # 'allauth.socialaccount.providers.facebook',
    # ...
    'django.contrib.sites',
    'bootstrap3', # django-bootstrap3
    # 'bootstrapform', # django-bootstrap-form

    'lab',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware', # tmp relax for "ajax" view.
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

# http://www.postgresql.org/docs/8.1/static/datetime-keywords.html#DATETIME-TIMEZONE-SET-TABLE
# http://en.wikipedia.org/wiki/List_of_tz_database_time_zones
TIME_ZONE = 'Mexico/General'
USE_TZ = False

USE_I18N = True
USE_L10N = True
LANGUAGE_CODE = 'en-us' # 'es-mx'

STATIC_URL = '/static/'
statics = os.path.join(BASE_DIR, 'static')
# STATIC_ROOT = statics # uncomment for collectstatic, and comment statics in STATICFILES_DIRS below.

TEMPLATE_DIRS = (
    os.path.join(BASE_DIR, 'templates'),

    os.path.join(BASE_DIR, 'allauthdemo', 'templates', 'plain', 'example'),
    os.path.join(BASE_DIR, 'allauthdemo', 'templates', 'allauth'),
    os.path.join(BASE_DIR, 'allauthdemo', 'templates'),
)

STATICFILES_DIRS = (
    statics,
)

REST_FRAMEWORK = {
    # 'PAGINATE_BY': 10

    # http://www.django-rest-framework.org/api-guide/authentication
    'DEFAULT_AUTHENTICATION_CLASSES': (
        # 'rest_framework.authentication.BasicAuthentication', # http://stackoverflow.com/questions/17665035/logout-not-working
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework_jwt.authentication.JSONWebTokenAuthentication',
    ),

    # http://www.django-rest-framework.org/api-guide/permissions
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAdminUser', # AllowAny / IsAuthenticated / IsAdminUser / DjangoModelPermissions
    ),
}

# https://github.com/GetBlimp/django-rest-framework-jwt
JWT_AUTH = {
    'JWT_EXPIRATION_DELTA': datetime.timedelta(seconds=1 * 60),
}

# https://github.com/GetBlimp/django-rest-framework-jwt
'''
$.post(
    'http://localhost:8000/api-token-auth/',
    { email: 'admin@go.com', password: 'admin' },
    function(data){
        $.ajax({
            url: 'http://localhost:8000/lab/api/users/',
            headers: { Authorization: 'JWT ' + data.token }
        })
    },
    'json'
)
'''
# same as above but as interval with same token.
'''
$.post(
  'http://localhost:8000/api-token-auth/',
  { email: 'admin@go.com', password: 'admin' },
  function(data){
    xTOKEN = data.token
    xSTART = new Date().getTime()
  },
  'json'
)
setInterval(
  function(){
    var diff = new Date().getTime() - xSTART
    console.log(_('Time: %s').sprintf(diff / 1000 / 60))
    $.ajax(
      { url: 'http://localhost:8000/lab/api/users/',
       headers: { Authorization: 'JWT ' + xTOKEN }
    })
  },
  3000
)
'''

# allauth.
TEMPLATE_CONTEXT_PROCESSORS += (
    'django.core.context_processors.request',
    'allauth.account.context_processors.account',
    'allauth.socialaccount.context_processors.socialaccount',
)
AUTHENTICATION_BACKENDS += (
    "allauth.account.auth_backends.AuthenticationBackend",
)
SITE_ID = 1
ACCOUNT_SESSION_REMEMBER = True
ACCOUNT_LOGOUT_REDIRECT_URL = '/accounts/login/'
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_PASSWORD_MIN_LENGTH = 1
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
AUTH_USER_MODEL = 'lab.User'
LOGIN_REDIRECT_URL = '/member/'


MPTT_ADMIN_LEVEL_INDENT = 20


SUIT_CONFIG = dict(
    ADMIN_NAME = 'Medical Visits DEMO',
    # HEADER_DATE_FORMAT = 'l, j. F Y',
    # HEADER_TIME_FORMAT = 'H:i',

    # SHOW_REQUIRED_ASTERISK = True,
    # CONFIRM_UNSAVED_CHANGES = True,

    # SEARCH_URL = '/admin/lab/user/', # http://django-suit.readthedocs.org/en/develop/configuration.html#search-url

    # MENU_ICONS: dict(
    #    sites = 'icon-leaf',
    #    auth = 'icon-lock',
    # ),
    # MENU_OPEN_FIRST_CHILD = True,
    # MENU_EXCLUDE = ('auth.group',),
    # MENU = (
    #     'sites',
    #     dict(app='auth', icon='icon-lock', models=('user', 'group')),
    #     dict(label='Settings', icon='icon-cog', models=('auth.user', 'auth.group')),
    #     dict(label='Support', icon='icon-question-sign', url='/support/'),
    # ),

    # LIST_PER_PAGE = 15,

    MENU = (
        dict(label='Site', icon='icon-cog', models=('account.emailconfirmation', 'account.emailaddress', 'sites.site')),
        dict(label='Geos', icon='icon-cog', app='lab', models=('country', 'state', 'city', 'brick', 'zip')),
        dict(label='Cats', icon='icon-cog', app='lab', models=('usercat', 'itemcat', 'loccat', 'formcat')),
        dict(label='Lab', icon='icon-cog', app='lab', models=('user', 'forcenode', 'forcevisit', 'item', 'loc', 'form', 'formfield')),
        # dict(label='ALL', icon='icon-cog', app='lab'),
    ),
)

# https://docs.djangoproject.com/en/1.6/topics/email/#console-backend
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

try:
    from settings_server import *
except ImportError:
    pass

# \lab\mysite> python manage.py graph_models lab -g -o models_lab.png
