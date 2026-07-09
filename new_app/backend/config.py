import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'aljwahrh-api-secret-key-2024')
    JWT_EXPIRY_HOURS = 24
    
    # Use PostgreSQL in production, SQLite in development
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if DATABASE_URL:
        # Render provides postgres:// but SQLAlchemy needs postgresql://
        if DATABASE_URL.startswith('postgres://'):
            DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    else:
        _db_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(_db_dir, 'instance', 'aljwahrh_land.db')
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
