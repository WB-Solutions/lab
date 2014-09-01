import os
from django.conf.global_settings import TEMPLATE_CONTEXT_PROCESSORS as TCP

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

SECRET_KEY = '^d0!gm53217iw3jqr66svdtw$oc-$#5b+x7p)xc+5+m-ekvxf1'

DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []

INSTALLED_APPS = (
    'suit',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'django_extensions',
    'rest_framework',

    'mptt',
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

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = False

STATIC_URL = '/static/'
statics = os.path.join(BASE_DIR, 'static')
# STATIC_ROOT = statics # uncomment for collectstatic, and comment statics in STATICFILES_DIRS below.

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

TEMPLATE_CONTEXT_PROCESSORS = TCP + (
    'django.core.context_processors.request',
)

SUIT_CONFIG = dict(
    ADMIN_NAME = 'Medical Visits DEMO',
    # HEADER_DATE_FORMAT = 'l, j. F Y',
    # HEADER_TIME_FORMAT = 'H:i',

    # SHOW_REQUIRED_ASTERISK = True,
    # CONFIRM_UNSAVED_CHANGES = True,

    SEARCH_URL = '/admin/lab/user/', # http://django-suit.readthedocs.org/en/develop/configuration.html#search-url
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
        dict(label='Users', icon='icon-cog', app='lab', models=('user',)),
        dict(label='Geos', icon='icon-cog', app='lab', models=('loc', 'loccat', 'country', 'state', 'city', 'brick', 'zip')),
        dict(label='Forces', icon='icon-cog', app='lab', models=('force', 'forcemgr', 'forcerep', 'forcevisit')),
        dict(label='Doctors', icon='icon-cog', app='lab', models=('doctor', 'doctorloc', 'doctorcat', 'doctorspecialty')),
        dict(label='Markets', icon='icon-cog', app='lab', models=('market', 'marketcat')),
        dict(label='Items', icon='icon-cog', app='lab', models=('item', 'itemcat', 'itemsubcat')),
        dict(label='Forms', icon='icon-cog', app='lab', models=('form', 'formfield')),
        # dict(label='ALL', icon='icon-cog', app='lab'),
    ),
)
