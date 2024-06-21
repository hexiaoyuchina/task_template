"""
Django settings for task_template project.

Generated by 'django-admin startproject' using Django 4.2.13.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""
import os
from datetime import timedelta
from kombu import Queue, Exchange
from pathlib import Path
import environ

BASE_DIR = environ.Path(__file__) - 2  # (qos_template/qos_template/settings.py - 2 = qos_template/)
# Load operating system environment variables and then prepare to use them
env = environ.Env()
env_file = "config/envs/%s.env" % env.str("PROJECT_ENV", "local")
env_path = BASE_DIR(env_file)
print("load env %s" % env_path)
env.read_env(env_path)


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-o#n2yw*5qimf_ou!%s)os!my5t)m1eogs%l)tq%j7*(s6_z$+u'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'workflow',
    'models'
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

ROOT_URLCONF = 'task_template.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates']
        ,
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

WSGI_APPLICATION = 'task_template.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases
env.ENVIRON['DB_URL'] = env.ENVIRON['DB_URL']
env.ENVIRON['DB_URL_QOS_TEMPLATE'] = env.ENVIRON['DB_URL_QOS_TEMPLATE']
# mysql db reconnect
env.DB_SCHEMES["mysql"] = "common.db_retry.backends.mysql"
DATABASES = {
    'default': env.db_url('DB_URL_QOS_TEMPLATE'),
    'task': env.db_url('DB_URL_QOS_TEMPLATE')
}

DATABASE_ROUTERS = [
    'common.db_router.DBRouter',
]
DATABASE_APPS_MAPPING = {
    "task": "task"
}

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Celery settings

CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://127.0.0.1:6379/1")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_BROKER_URL", "redis://127.0.0.1:6379/1")
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
# 任务结果过期时间
CELERY_RESULT_EXPIRES = 60 * 60
# CELERY_TIMEZONE = 'Asia/Shanghai'
CELERY_ENABLE_UTC = True
CELERY_TASK_TIME_LIMIT = 60 * 60

CELERY_TASK_QUEUES = (
    Queue('workflow', Exchange('tasks', 'topic'), routing_key='workflow.#'),
    Queue('task', Exchange('tasks', 'topic'), routing_key='task.#'),
)

# 定义celery定时
CELERY_BEAT_SCHEDULE = {
    'task_nsx': {
        'task': 'workflows.core.producer.produce_workflows',
        'schedule': timedelta(seconds=5),
        'options': {
            'queue': 'workflow'
        }
    }
}

BROKER_TRANSPORT_OPTIONS = {"socket_keepalive": True, "health_check_interval": 4}