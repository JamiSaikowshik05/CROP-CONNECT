"""
Django settings for CropConnect — Direct Crop Procurement Portal
"""
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-only-change-me')
DEBUG = os.environ.get('DEBUG', 'True').lower() in {'1', 'true', 'yes'}
if not DEBUG and SECRET_KEY == 'dev-only-change-me':
    from django.core.exceptions import ImproperlyConfigured
    raise ImproperlyConfigured('Set the SECRET_KEY environment variable before running with DEBUG=0.')

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '.onrender.com']
if os.environ.get('RENDER_EXTERNAL_HOSTNAME'):
    ALLOWED_HOSTS.append(os.environ['RENDER_EXTERNAL_HOSTNAME'])
ALLOWED_HOSTS += [h.strip() for h in os.environ.get('ALLOWED_HOSTS', '').split(',') if h.strip()]
CSRF_TRUSTED_ORIGINS = ['https://*.onrender.com'] + [
    o.strip() for o in os.environ.get('CSRF_TRUSTED_ORIGINS', '').split(',') if o.strip()
]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'procurement',
]

AUTH_USER_MODEL = 'procurement.User'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'e_paddy_portal.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.template.context_processors.i18n',
                'procurement.context_processors.nav_languages',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'e_paddy_portal.wsgi.application'

# ── DATABASE ──────────────────────────────────────────────────
# Default: MySQL 8. Set these environment variables (see DEPLOY.md):
#   DB_NAME (default cropconnect), DB_USER, DB_PASSWORD, DB_HOST, DB_PORT
#   Hosted MySQL (Aiven): also DB_SSL_CA_PEM (the CA certificate text) or DB_SSL_CA (a file path)
# Or one value:  DATABASE_URL=mysql://user:password@host:3306/cropconnect
# SQLite is used only when you explicitly set DB_ENGINE=sqlite (quick tests).
DB_ENGINE = os.environ.get('DB_ENGINE', 'mysql').lower()
if os.environ.get('DATABASE_URL'):
    import dj_database_url
    DATABASES = {'default': dj_database_url.config(conn_max_age=600)}
elif DB_ENGINE == 'sqlite':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    _db_host = os.environ.get('DB_HOST', '127.0.0.1')
    # Hosted MySQL services such as Aiven require encrypted connections and a CA certificate.
    # Provide the certificate either as a file (DB_SSL_CA) or as its text (DB_SSL_CA_PEM).
    _ca_pem = os.environ.get('DB_SSL_CA_PEM', '').replace('\\n', '\n').strip()
    _ca_file = os.environ.get('DB_SSL_CA', '')
    if _ca_pem:
        import tempfile
        _ca_file = os.path.join(tempfile.gettempdir(), 'cropconnect-db-ca.pem')
        with open(_ca_file, 'w', encoding='utf-8') as _ca_out:
            _ca_out.write(_ca_pem + '\n')
    _local = _db_host in ('127.0.0.1', 'localhost', '::1')
    _ssl_default = '' if (_local and not _ca_file) else '1'
    _ssl_wanted = os.environ.get('DB_SSL', _ssl_default).lower() in {'1', 'true', 'yes', 'required'}
    _mysql_options = {
        'charset': 'utf8mb4',   # required for Indian scripts (Telugu, Hindi, Tamil ...)
        'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
    }
    if _ca_file:
        _mysql_options['ssl_ca'] = _ca_file
    if _ssl_wanted:
        _mysql_options['ssl_disabled'] = False
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.environ.get('DB_NAME', 'cropconnect'),
            'USER': os.environ.get('DB_USER', 'root'),
            'PASSWORD': os.environ.get('DB_PASSWORD', ''),
            'HOST': _db_host,
            'PORT': os.environ.get('DB_PORT', '3306'),
            'OPTIONS': _mysql_options,
        }
    }

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en'
# Shown in the language picker. Name is written in the language's own script.
LANGUAGES = [
    ('en', 'English'),
    ('hi', 'हिन्दी'),              # Hindi
    ('te', 'తెలుగు'),              # Telugu
    ('ta', 'தமிழ்'),               # Tamil
    ('bn', 'বাংলা'),               # Bengali
    ('mr', 'मराठी'),               # Marathi
    ('gu', 'ગુજરાતી'),              # Gujarati
    ('kn', 'ಕನ್ನಡ'),              # Kannada
    ('ml', 'മലയാളം'),              # Malayalam
    ('pa', 'ਪੰਜਾਬੀ'),              # Punjabi
    ('or', 'ଓଡ଼ିଆ'),              # Odia
    ('as', 'অসমীয়া'),             # Assamese
    ('ur', 'اردو'),               # Urdu
    ('sd', 'سنڌي'),               # Sindhi
    ('ks', 'کٲشُر'),              # Kashmiri
    ('ne', 'नेपाली'),              # Nepali
    ('sa', 'संस्कृतम्'),           # Sanskrit
    ('mai', 'मैथिली'),             # Maithili
    ('doi', 'डोगरी'),              # Dogri
    ('brx', 'बड़ो'),               # Bodo
    ('kok', 'कोंकणी'),             # Konkani
    ('sat', 'ᱥᱟᱱᱛᱟᱲᱤ'),            # Santali
    ('mni', 'ꯃꯤꯇꯩꯂꯣꯟ'),          # Manipuri (Meitei)
]
LANGUAGES_BIDI = ['ur', 'sd', 'ks']
LOCALE_PATHS = [BASE_DIR / 'locale']
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# ── AI Configuration ──
# Get your free API key from: https://console.anthropic.com
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')

STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage'},
}
