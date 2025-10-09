import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'jewel-land-cleaning-company-secret-key-2024'

    # استخدام PostgreSQL على Render أو SQLite محلياً
    if os.environ.get('DATABASE_URL'):
        SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL').replace('postgres://', 'postgresql://')
    else:
        BASE_DIR = os.path.abspath(os.path.dirname(__file__))
        instance_path = os.path.join(BASE_DIR, 'instance')
        if not os.path.exists(instance_path):
            os.makedirs(instance_path)
        SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(instance_path, 'cleaning_company.db')

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 300,
        'pool_pre_ping': True,
        'connect_args': {'check_same_thread': False} if 'sqlite' in SQLALCHEMY_DATABASE_URI else {}
    }

    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    SESSION_COOKIE_SECURE = not DEBUG
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    PREFERRED_URL_SCHEME = 'https' if not DEBUG else 'http'
