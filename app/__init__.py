"""
Flask Application Factory
نظام تقسيط - إدارة مبيعات التقسيط
"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate

from app.config import config

# تهيئة الإضافات
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
migrate = Migrate()


def create_app(config_name='default'):
    """إنشاء وتهيئة التطبيق"""
    app = Flask(__name__)

    # تحميل الإعدادات
    app.config.from_object(config[config_name])

    # تهيئة الإضافات
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)

    # إعدادات تسجيل الدخول
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'يرجى تسجيل الدخول للوصول لهذه الصفحة'
    login_manager.login_message_category = 'warning'

    # تسجيل Blueprints
    from app.controllers.auth import auth_bp
    from app.controllers.dashboard import dashboard_bp
    from app.controllers.products import products_bp
    from app.controllers.categories import categories_bp
    from app.controllers.customers import customers_bp
    from app.controllers.invoices import invoices_bp
    from app.controllers.installments import installments_bp
    from app.controllers.payments import payments_bp
    from app.controllers.users import users_bp
    from app.controllers.reports import reports_bp
    from app.controllers.settings import settings_bp
    from app.controllers.api import api_bp
    from app.controllers.api import v2  # ضمان تحميل routes

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(products_bp, url_prefix='/products')
    app.register_blueprint(categories_bp, url_prefix='/categories')
    app.register_blueprint(customers_bp, url_prefix='/customers')
    app.register_blueprint(invoices_bp, url_prefix='/invoices')
    app.register_blueprint(installments_bp, url_prefix='/installments')
    app.register_blueprint(payments_bp, url_prefix='/payments')
    app.register_blueprint(users_bp, url_prefix='/users')
    app.register_blueprint(reports_bp, url_prefix='/reports')
    app.register_blueprint(settings_bp, url_prefix='/settings')
    app.register_blueprint(api_bp, url_prefix='/api/v2')

    # تسجيل Context Processors
    from app.utils.helpers import (
        format_money, format_date, format_datetime,
        invoice_type_label, invoice_status_label, installment_status_label,
        user_role_label, payment_method_label
    )

    @app.context_processor
    def utility_processor():
        """إضافة دوال مساعدة للقوالب"""
        from app.models.setting import Setting
        settings = {}
        try:
            settings = Setting.get_all_dict()
        except:
            pass

        return {
            'format_money': format_money,
            'format_date': format_date,
            'format_datetime': format_datetime,
            'invoice_type': invoice_type_label,
            'invoice_status': invoice_status_label,
            'installment_status': installment_status_label,
            'user_role': user_role_label,
            'payment_method': payment_method_label,
            'settings': settings,
            'app_name': app.config.get('APP_NAME', 'نظام تقسيط'),
            'currency': app.config.get('CURRENCY', 'ج.م'),
        }

    # معالجة الأخطاء
    @app.errorhandler(404)
    def not_found_error(error):
        return {'error': 'الصفحة غير موجودة'}, 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return {'error': 'خطأ في الخادم'}, 500

    return app
