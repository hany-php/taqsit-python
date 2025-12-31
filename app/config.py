"""
إعدادات التطبيق
"""
import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    """الإعدادات الأساسية"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'

    # إعدادات قاعدة البيانات
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql+psycopg://postgres:password@localhost:5432/taqsit_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }

    # إعدادات الجلسة
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # إعدادات التطبيق
    APP_NAME = os.environ.get('APP_NAME') or 'نظام تقسيط'
    CURRENCY = os.environ.get('CURRENCY') or 'ج.م'

    # إعدادات الملفات
    UPLOAD_FOLDER = 'app/static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

    # إعدادات Pagination
    ITEMS_PER_PAGE = 10


class DevelopmentConfig(Config):
    """إعدادات التطوير"""
    DEBUG = True


class ProductionConfig(Config):
    """إعدادات الإنتاج"""
    DEBUG = False
    SESSION_COOKIE_SECURE = True


class TestingConfig(Config):
    """إعدادات الاختبار"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
