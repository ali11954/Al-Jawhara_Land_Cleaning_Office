import os


class Config:
    # مفتاح الأمان للتطبيق
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'jewel-land-cleaning-company-secret-key-2024'

    # قاعدة البيانات
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///cleaning_company.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # إعدادات التطبيق
    DEBUG = True
    TESTING = False

    # إعدادات الجلسة
    SESSION_COOKIE_SECURE = False  # ضع True في الإنتاج مع HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # إعدادات التحميل
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB كحد أقصى للتحميل