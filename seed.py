"""
سكريبت لإنشاء البيانات الأولية
"""
from app.models.setting import Setting
from app.models.category import Category
from app.models.user import User
from app import create_app, db
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def create_initial_data():
    """إنشاء البيانات الأولية"""
    app = create_app()

    with app.app_context():
        # التحقق من وجود مستخدم admin
        admin = User.query.filter_by(username='admin').first()

        if not admin:
            admin = User(
                username='admin',
                full_name='مدير النظام',
                email='admin@taqsit.local',
                phone='01000000000',
                role='admin',
                is_active=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            print('✓ تم إنشاء المستخدم الإداري (admin / admin123)')
        else:
            print('○ المستخدم الإداري موجود بالفعل')

        # إنشاء تصنيفات افتراضية
        default_categories = [
            {'name': 'أجهزة كهربائية', 'icon': 'electrical_services', 'color': '#1e88e5'},
            {'name': 'موبايلات', 'icon': 'phone_iphone', 'color': '#10b981'},
            {'name': 'أثاث منزلي', 'icon': 'chair', 'color': '#f59e0b'},
            {'name': 'إلكترونيات', 'icon': 'devices', 'color': '#ef4444'},
        ]

        for cat_data in default_categories:
            if not Category.query.filter_by(name=cat_data['name']).first():
                cat = Category(**cat_data)
                db.session.add(cat)
                print(f'✓ تم إنشاء التصنيف: {cat_data["name"]}')

        # إعدادات افتراضية
        default_settings = [
            ('store_name', 'نظام تقسيط'),
            ('store_phone', '01000000000'),
            ('store_address', 'مصر'),
            ('currency', 'ج.م'),
            ('default_installment_months', '12'),
            ('late_fee_percentage', '0'),
        ]

        for key, value in default_settings:
            Setting.set(key, value)
        print('✓ تم تحديث الإعدادات الافتراضية')

        db.session.commit()
        print('\n✅ تم إنشاء البيانات الأولية بنجاح!')
        print('\n📋 بيانات الدخول:')
        print('   اسم المستخدم: admin')
        print('   كلمة المرور: admin123')


if __name__ == '__main__':
    create_initial_data()
