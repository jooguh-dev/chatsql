import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'change-me')
DEBUG = os.getenv('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Anthropic mode: 'mock' (default) or 'real'. Use 'mock' to conserve credits during demos.
ANTHROPIC_MODE = os.getenv('ANTHROPIC_MODE', 'mock')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'exercises',
    'ai_tutor',
    'accounts',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'chatsql.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'chatsql.wsgi.application'

# Databases
DB_NAME = os.getenv('DB_NAME')

# GCP Cloud SQL Configuration
GCP_DB_HOST = os.getenv('GCP_DB_HOST')
GCP_DB_USER = os.getenv('GCP_DB_USER')
GCP_DB_PASSWORD = os.getenv('GCP_DB_PASSWORD')
GCP_DB_PORT = os.getenv('GCP_DB_PORT', '3306')
GCP_INSTANCE_CONNECTION_NAME = os.getenv('GCP_INSTANCE_CONNECTION_NAME')  # 格式: project:region:instance

def get_gcp_db_config(db_name: str):
    """生成GCP Cloud SQL数据库配置"""
    return {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': db_name,
        'USER': GCP_DB_USER,
        'PASSWORD': GCP_DB_PASSWORD,
        'HOST': GCP_DB_HOST,
        'PORT': GCP_DB_PORT,
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
        }
    }

# If GCP_DB_HOST is provided, configure GCP Cloud SQL databases
# Otherwise, check for legacy DB_NAME or fall back to SQLite
if GCP_DB_HOST:
    # GCP Cloud SQL配置
    DATABASES = {
        'default': get_gcp_db_config('chatsql_system'),
    }
    
    # 动态题目数据库会在运行时通过executor动态连接
    # 这里不预定义所有chatsql_problem_N数据库，而是通过动态配置
elif DB_NAME:
    # Legacy MySQL配置（向后兼容）
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.getenv('DB_NAME'),
            'USER': os.getenv('DB_USER'),
            'PASSWORD': os.getenv('DB_PASSWORD'),
            'HOST': os.getenv('DB_HOST'),
            'PORT': os.getenv('DB_PORT', '3306'),
            'OPTIONS': {
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
                'charset': 'utf8mb4',
            }
        },
        'practice_hr': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'practice_hr',
            'USER': os.getenv('PRACTICE_DB_USER'),
            'PASSWORD': os.getenv('PRACTICE_DB_PASSWORD'),
            'HOST': os.getenv('PRACTICE_DB_HOST'),
            'PORT': '3306',
        },
        'practice_ecommerce': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'practice_ecommerce',
            'USER': os.getenv('PRACTICE_DB_USER'),
            'PASSWORD': os.getenv('PRACTICE_DB_PASSWORD'),
            'HOST': os.getenv('PRACTICE_DB_HOST'),
            'PORT': '3306',
        },
        'practice_school': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'practice_school',
            'USER': os.getenv('PRACTICE_DB_USER'),
            'PASSWORD': os.getenv('PRACTICE_DB_PASSWORD'),
            'HOST': os.getenv('PRACTICE_DB_HOST'),
            'PORT': '3306',
        }
    }
else:
    # Local development fallback
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

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

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = '/static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS Configuration
# IMPORTANT: When CORS_ALLOW_ALL_ORIGINS = True, CORS_ALLOW_CREDENTIALS must be False
# This is a security requirement by django-cors-headers
# Since frontend uses credentials: 'include', we must use specific origins
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOW_CREDENTIALS = True  # Required for credentials: 'include' in frontend
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3002",
    "http://127.0.0.1:3002",
]

# Additional CORS settings for development
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'chatsql.authentication.CsrfExemptSessionAuthentication',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
}

# Session Cookie配置 - 支持跨域请求
# 注意：SameSite='None'需要Secure=True，但localhost开发环境Secure=False可能不工作
# 对于localhost，尝试使用Lax（允许同站请求）
# 如果使用代理（vite proxy），Lax应该可以工作
SESSION_COOKIE_SAMESITE = 'Lax'  # 对于localhost开发环境，Lax可能更可靠
SESSION_COOKIE_SECURE = False  # 开发环境可以是False
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = 86400 * 7  # 7天
SESSION_SAVE_EVERY_REQUEST = True  # 每次请求都保存session，确保cookie不会丢失
SESSION_COOKIE_DOMAIN = None  # None表示使用当前域名
SESSION_COOKIE_PATH = '/'  # Cookie路径

# CSRF Cookie配置
CSRF_COOKIE_SAMESITE = 'None'
CSRF_COOKIE_SECURE = False

CSRF_TRUSTED_ORIGINS = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    'http://localhost:3002',
    'http://127.0.0.1:3002',
]
