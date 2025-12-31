"""
نقطة تشغيل التطبيق
"""
import os
from app import create_app, db
from app.models import User, Category, Product, Customer, Invoice, Installment, Payment, Setting

# إنشاء التطبيق
app = create_app(os.environ.get('FLASK_ENV') or 'development')


@app.shell_context_processor
def make_shell_context():
    """إضافة كائنات للـ Flask Shell"""
    return {
        'db': db,
        'User': User,
        'Category': Category,
        'Product': Product,
        'Customer': Customer,
        'Invoice': Invoice,
        'Installment': Installment,
        'Payment': Payment,
        'Setting': Setting,
    }


@app.cli.command('init-db')
def init_db():
    """إنشاء قاعدة البيانات والجداول"""
    db.create_all()
    
    # إضافة مستخدم افتراضي
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            full_name='مدير النظام',
            role='admin',
            is_active=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        
        # إضافة إعدادات افتراضية
        default_settings = [
            ('store_name', 'متجر تقسيط', 'general'),
            ('store_phone', '01000000000', 'general'),
            ('store_address', 'العنوان', 'general'),
            ('currency', 'ج.م', 'general'),
            ('default_installment_months', '12', 'installment'),
            ('late_fee_percentage', '0', 'installment'),
        ]
        
        for key, value, group in default_settings:
            if not Setting.query.filter_by(setting_key=key).first():
                setting = Setting(
                    setting_key=key,
                    setting_value=value,
                    setting_group=group
                )
                db.session.add(setting)
        
        db.session.commit()
        print('تم إنشاء قاعدة البيانات وإضافة البيانات الافتراضية')
    else:
        print('قاعدة البيانات موجودة مسبقاً')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
