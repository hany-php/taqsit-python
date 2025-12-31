"""
سكريبت إضافة بيانات تجريبية شاملة
1000+ منتج، عملاء، فواتير، أقساط
"""
from app.models.setting import Setting
from app.models.payment import Payment
from app.models.installment import Installment
from app.models.invoice import Invoice, InvoiceItem
from app.models.customer import Customer
from app.models.product import Product
from app.models.category import Category
from app.models.user import User
from app import create_app, db
import sys
import os
import random
from datetime import datetime, timedelta, date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# بيانات المنتجات حسب التصنيف
PRODUCTS_DATA = {
    'أجهزة كهربائية': [
        ('ثلاجة', 8000, 10000), ('غسالة', 6000, 8000), ('مكيف', 12000, 15000),
        ('سخان مياه', 2000, 3000), ('ميكروويف', 1500, 2500), ('خلاط', 500, 800),
        ('مكنسة كهربائية', 1200, 1800), ('بوتاجاز',
                                         4000, 6000), ('شفاط', 1500, 2500),
        ('ديب فريزر', 5000, 7000), ('مكواة', 400, 700), ('محضرة طعام', 800, 1200),
        ('سخان كهربائي', 600, 1000), ('مروحة', 300, 600), ('دفاية', 800, 1400),
    ],
    'موبايلات': [
        ('iPhone 15 Pro Max', 50000, 60000), ('iPhone 15 Pro', 45000, 55000),
        ('iPhone 15', 35000, 42000), ('iPhone 14', 28000, 35000),
        ('Samsung S24 Ultra', 48000, 58000), ('Samsung S24+', 40000, 50000),
        ('Samsung S24', 32000, 40000), ('Samsung A54', 12000, 16000),
        ('Xiaomi 14', 20000, 26000), ('Xiaomi 13', 15000, 20000),
        ('Oppo Reno 11', 18000, 24000), ('Vivo X90', 22000, 28000),
        ('Huawei P60', 25000, 32000), ('Realme GT3', 14000, 18000),
        ('OnePlus 12', 28000, 36000), ('Google Pixel 8', 30000, 38000),
    ],
    'أثاث منزلي': [
        ('غرفة نوم كاملة', 25000, 35000), ('غرفة سفرة', 15000, 22000),
        ('صالون', 12000, 18000), ('أنتريه', 8000, 12000), ('مطبخ', 20000, 30000),
        ('سرير مفرد', 3000, 5000), ('سرير مزدوج',
                                    5000, 8000), ('دولاب', 4000, 7000),
        ('كنبة', 6000, 10000), ('طاولة طعام', 3000, 5000), ('مكتب', 2000, 4000),
        ('كرسي مكتب', 1000, 2000), ('رف كتب', 800,
                                    1500), ('ستاند تلفزيون', 1500, 3000),
    ],
    'إلكترونيات': [
        ('تلفزيون 65 بوصة', 18000, 25000), ('تلفزيون 55 بوصة', 12000, 18000),
        ('تلفزيون 50 بوصة', 8000, 12000), ('تلفزيون 43 بوصة', 6000, 9000),
        ('لابتوب HP', 15000, 22000), ('لابتوب Dell', 18000, 25000),
        ('لابتوب Lenovo', 12000, 18000), ('لابتوب MacBook', 40000, 55000),
        ('PlayStation 5', 22000, 28000), ('Xbox Series X', 20000, 26000),
        ('سماعات', 500, 1500), ('ساوند بار', 3000, 6000), ('كاميرا', 8000, 15000),
        ('طابعة', 2000, 4000), ('راوتر', 500, 1200), ('هارد ديسك', 1000, 2500),
    ],
}

# أسماء العملاء
FIRST_NAMES = ['محمد', 'أحمد', 'علي', 'حسن', 'إبراهيم', 'عمر', 'خالد', 'يوسف', 'عبدالله', 'مصطفى',
               'فاطمة', 'عائشة', 'مريم', 'نور', 'سارة', 'هند', 'ليلى', 'أمل', 'دينا', 'رنا']
LAST_NAMES = ['محمد', 'أحمد', 'علي', 'حسن', 'إبراهيم', 'السيد', 'الشريف', 'عبدالرحمن', 'الفارس', 'النجار',
              'الحداد', 'البكري', 'العمري', 'الخطيب', 'السعيد', 'المهدي', 'الأمين', 'الكريم', 'الرشيد', 'المختار']

CITIES = ['القاهرة', 'الإسكندرية', 'الجيزة', 'المنصورة',
          'طنطا', 'الزقازيق', 'أسيوط', 'سوهاج', 'بني سويف', 'الفيوم']


def generate_phone():
    return f"01{random.choice(['0', '1', '2', '5'])}{random.randint(10000000, 99999999)}"


def generate_national_id():
    return f"{random.randint(2, 3)}{random.randint(10000000000000, 99999999999999)}"[:14]


def create_sample_data():
    """إنشاء البيانات التجريبية"""
    app = create_app()

    with app.app_context():
        print('🚀 بدء إنشاء البيانات التجريبية...\n')

        # التحقق من وجود المستخدم admin
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
            db.session.commit()
            print('✅ تم إنشاء المستخدم الإداري')

        # إنشاء موظف مبيعات
        sales_user = User.query.filter_by(username='sales').first()
        if not sales_user:
            sales_user = User(
                username='sales',
                full_name='موظف المبيعات',
                email='sales@taqsit.local',
                phone='01100000000',
                role='sales',
                is_active=True
            )
            sales_user.set_password('sales123')
            db.session.add(sales_user)
            db.session.commit()
            print('✅ تم إنشاء موظف المبيعات')

        # إنشاء التصنيفات
        categories = {}
        category_colors = {
            'أجهزة كهربائية': '#1e88e5',
            'موبايلات': '#10b981',
            'أثاث منزلي': '#f59e0b',
            'إلكترونيات': '#ef4444',
        }
        category_icons = {
            'أجهزة كهربائية': 'electrical_services',
            'موبايلات': 'phone_iphone',
            'أثاث منزلي': 'chair',
            'إلكترونيات': 'devices',
        }

        for cat_name in PRODUCTS_DATA.keys():
            cat = Category.query.filter_by(name=cat_name).first()
            if not cat:
                cat = Category(
                    name=cat_name,
                    icon=category_icons.get(cat_name, 'category'),
                    color=category_colors.get(cat_name, '#1e88e5'),
                    is_active=True
                )
                db.session.add(cat)
                db.session.commit()
            categories[cat_name] = cat

        print(f'✅ تم إنشاء {len(categories)} تصنيفات')

        # إنشاء المنتجات (1000+ منتج)
        products_created = 0
        all_products = []

        for cat_name, products_list in PRODUCTS_DATA.items():
            category = categories[cat_name]

            # إنشاء نسخ متعددة من كل منتج
            for base_name, cost_min, cost_max in products_list:
                # إنشاء 15-20 منتج من كل نوع
                for i in range(random.randint(15, 20)):
                    suffix = f" - {random.choice(['اقتصادي', 'عادي', 'ممتاز', 'فاخر', 'سوبر'])}" if i > 0 else ""
                    product_name = f"{base_name}{suffix}"

                    if Product.query.filter_by(name=product_name, category_id=category.id).first():
                        continue

                    cost_price = random.randint(cost_min, cost_max)
                    cash_price = int(cost_price * random.uniform(1.15, 1.30))
                    installment_price = int(
                        cash_price * random.uniform(1.10, 1.25))

                    product = Product(
                        name=product_name,
                        description=f"منتج {base_name} عالي الجودة",
                        barcode=f"{category.id}{random.randint(100000, 999999)}",
                        category_id=category.id,
                        cost_price=cost_price,
                        cash_price=cash_price,
                        installment_price=installment_price,
                        quantity=random.randint(5, 50),
                        min_quantity=3,
                        is_active=True
                    )
                    db.session.add(product)
                    all_products.append(product)
                    products_created += 1

        db.session.commit()
        print(f'✅ تم إنشاء {products_created} منتج')

        # إعادة تحميل المنتجات
        all_products = Product.query.filter_by(is_active=True).all()

        # إنشاء العملاء (200 عميل)
        customers_created = 0
        all_customers = []

        for _ in range(200):
            full_name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)} {random.choice(LAST_NAMES)}"

            customer = Customer(
                full_name=full_name,
                phone=generate_phone(),
                phone2=generate_phone() if random.random() > 0.5 else None,
                national_id=generate_national_id(),
                address=f"{random.choice(CITIES)} - شارع {random.randint(1, 100)}",
                work_address=f"شركة {random.choice(['الأمل', 'النور', 'السلام', 'الفتح', 'المستقبل'])} - {random.choice(CITIES)}",
                work_phone=generate_phone() if random.random() > 0.5 else None,
                guarantor_name=f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
                guarantor_phone=generate_phone(),
                is_active=True
            )
            db.session.add(customer)
            all_customers.append(customer)
            customers_created += 1

        db.session.commit()
        print(f'✅ تم إنشاء {customers_created} عميل')

        # إعادة تحميل العملاء
        all_customers = Customer.query.filter_by(is_active=True).all()

        # إنشاء فواتير نقدية (100 فاتورة)
        cash_invoices = 0
        for _ in range(100):
            invoice_date = datetime.now() - timedelta(days=random.randint(0, 90))

            invoice = Invoice(
                invoice_number=Invoice.generate_invoice_number(),
                customer_id=random.choice(
                    all_customers).id if random.random() > 0.3 else None,
                user_id=random.choice([admin.id, sales_user.id]),
                invoice_type='cash',
                total_amount=0,
                paid_amount=0,
                status='completed',
                created_at=invoice_date
            )
            db.session.add(invoice)
            db.session.flush()

            # إضافة عناصر الفاتورة (1-5 منتجات)
            total = 0
            for _ in range(random.randint(1, 5)):
                product = random.choice(all_products)
                qty = random.randint(1, 3)

                item = InvoiceItem(
                    invoice_id=invoice.id,
                    product_id=product.id,
                    product_name=product.name,
                    quantity=qty,
                    unit_price=product.cash_price,
                    total_price=qty * product.cash_price
                )
                db.session.add(item)
                total += float(item.total_price)

            invoice.total_amount = total
            invoice.paid_amount = total
            cash_invoices += 1

        db.session.commit()
        print(f'✅ تم إنشاء {cash_invoices} فاتورة نقدية')

        # إنشاء فواتير تقسيط (150 فاتورة)
        installment_invoices = 0
        for _ in range(150):
            invoice_date = datetime.now() - timedelta(days=random.randint(0, 180))
            customer = random.choice(all_customers)
            months = random.choice([3, 6, 9, 12, 18, 24])

            invoice = Invoice(
                invoice_number=Invoice.generate_invoice_number(),
                customer_id=customer.id,
                user_id=random.choice([admin.id, sales_user.id]),
                invoice_type='installment',
                total_amount=0,
                down_payment=0,
                installment_months=months,
                status='active',
                created_at=invoice_date
            )
            db.session.add(invoice)
            db.session.flush()

            # إضافة عناصر الفاتورة
            total = 0
            for _ in range(random.randint(1, 4)):
                product = random.choice(all_products)
                qty = random.randint(1, 2)

                item = InvoiceItem(
                    invoice_id=invoice.id,
                    product_id=product.id,
                    product_name=product.name,
                    quantity=qty,
                    unit_price=product.installment_price,
                    total_price=qty * product.installment_price
                )
                db.session.add(item)
                total += float(item.total_price)

            # حساب الدفعة المقدمة
            down_payment = int(total * random.uniform(0.1, 0.3))
            remaining = total - down_payment
            monthly = remaining / months

            invoice.total_amount = total
            invoice.down_payment = down_payment
            invoice.paid_amount = down_payment
            invoice.remaining_amount = remaining
            invoice.monthly_installment = monthly

            # إنشاء الأقساط
            for i in range(months):
                due_date = invoice_date.date() + timedelta(days=30 * (i + 1))

                # تحديد حالة القسط
                if due_date < date.today():
                    status = random.choices(
                        ['paid', 'overdue'], weights=[0.7, 0.3])[0]
                elif due_date == date.today():
                    status = 'pending'
                else:
                    status = 'pending'

                installment = Installment(
                    invoice_id=invoice.id,
                    installment_number=i + 1,
                    amount=monthly,
                    remaining_amount=0 if status == 'paid' else monthly,
                    due_date=due_date,
                    status=status,
                    paid_date=due_date if status == 'paid' else None
                )
                db.session.add(installment)

                # إنشاء دفعة إذا كان القسط مدفوع
                if status == 'paid':
                    payment = Payment(
                        invoice_id=invoice.id,
                        installment_id=None,  # سيتم تحديثه لاحقاً
                        amount=monthly,
                        payment_method='cash',
                        receipt_number=f"RCP{random.randint(10000, 99999)}",
                        user_id=random.choice([admin.id, sales_user.id]),
                        payment_date=datetime.combine(
                            due_date, datetime.min.time())
                    )
                    db.session.add(payment)

            # تحديث حالة الفاتورة
            installment_invoices += 1

        db.session.commit()
        print(f'✅ تم إنشاء {installment_invoices} فاتورة تقسيط مع الأقساط')

        # تحديث الإعدادات
        settings = [
            ('store_name', 'نظام تقسيط الأمل'),
            ('store_phone', '01000000000'),
            ('store_address', 'القاهرة - مصر'),
            ('currency', 'ج.م'),
            ('default_installment_months', '12'),
        ]
        for key, value in settings:
            Setting.set(key, value)

        print('\n' + '='*50)
        print('✅ تم إنشاء البيانات التجريبية بنجاح!')
        print('='*50)
        print(f'📦 المنتجات: {Product.query.count()}')
        print(f'👥 العملاء: {Customer.query.count()}')
        print(
            f'🧾 الفواتير النقدية: {Invoice.query.filter_by(invoice_type="cash").count()}')
        print(
            f'📄 فواتير التقسيط: {Invoice.query.filter_by(invoice_type="installment").count()}')
        print(f'💳 الأقساط: {Installment.query.count()}')
        print(f'💰 المدفوعات: {Payment.query.count()}')
        print('='*50)
        print('\n📋 بيانات الدخول:')
        print('   مدير: admin / admin123')
        print('   موظف: sales / sales123')


if __name__ == '__main__':
    create_sample_data()
