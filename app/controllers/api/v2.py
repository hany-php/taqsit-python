"""
API v2 Controller - RESTful API متكاملة
"""
from datetime import date, datetime
from flask import request, jsonify
from app.controllers.api import api_bp
from app.models.product import Product
from app.models.category import Category
from app.models.customer import Customer
from app.models.invoice import Invoice, InvoiceItem
from app.models.installment import Installment
from app.models.payment import Payment
from app.models.activity_log import ActivityLog
from app.utils.decorators import api_key_required
from app import db


def api_response(success, data=None, message=None, error=None, status_code=200):
    """Helper function for consistent API responses"""
    response = {'success': success}
    if data is not None:
        response['data'] = data
    if message:
        response['message'] = message
    if error:
        response['error'] = error
    return jsonify(response), status_code


# =============== المنتجات (Products) ===============

@api_bp.route('/products', methods=['GET'])
@api_key_required
def get_products():
    """جلب جميع المنتجات"""
    page = request.args.get('page', 1, type=int)
    per_page = min(100, request.args.get('per_page', 20, type=int))
    search = request.args.get('q', '')
    category_id = request.args.get('category', type=int)

    query = Product.query.filter_by(is_active=True)

    if search:
        search_term = f'%{search}%'
        query = query.filter(
            db.or_(
                Product.name.ilike(search_term),
                Product.barcode.ilike(search_term)
            )
        )

    if category_id:
        query = query.filter_by(category_id=category_id)

    total = query.count()
    products = query.offset((page - 1) * per_page).limit(per_page).all()

    return jsonify({
        'success': True,
        'data': [p.to_dict() for p in products],
        'pagination': {
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        }
    })


@api_bp.route('/products/<int:id>', methods=['GET'])
@api_key_required
def get_product(id):
    """جلب منتج بالـ ID"""
    product = Product.query.get(id)

    if not product:
        return api_response(False, error='المنتج غير موجود', status_code=404)

    return api_response(True, data=product.to_dict())


@api_bp.route('/products', methods=['POST'])
@api_key_required
def create_product():
    """إضافة منتج جديد"""
    data = request.get_json()

    if not data:
        return api_response(False, error='بيانات غير صالحة', status_code=400)

    required_fields = ['name', 'price']
    for field in required_fields:
        if field not in data:
            return api_response(False, error=f'الحقل {field} مطلوب', status_code=400)

    try:
        product = Product(
            name=data['name'],
            barcode=data.get('barcode'),
            description=data.get('description'),
            category_id=data.get('category_id'),
            selling_price=data['price'],
            cost_price=data.get('cost_price', 0),
            quantity=data.get('stock_quantity', 0),
            min_stock=data.get('min_stock', 5),
            is_active=data.get('is_active', True)
        )

        db.session.add(product)
        db.session.commit()

        return api_response(True, data=product.to_dict(), message='تم إضافة المنتج بنجاح', status_code=201)

    except Exception as e:
        db.session.rollback()
        return api_response(False, error=str(e), status_code=500)


@api_bp.route('/products/<int:id>', methods=['PUT'])
@api_key_required
def update_product(id):
    """تحديث منتج"""
    product = Product.query.get(id)

    if not product:
        return api_response(False, error='المنتج غير موجود', status_code=404)

    data = request.get_json()

    if not data:
        return api_response(False, error='بيانات غير صالحة', status_code=400)

    try:
        if 'name' in data:
            product.name = data['name']
        if 'barcode' in data:
            product.barcode = data['barcode']
        if 'description' in data:
            product.description = data['description']
        if 'category_id' in data:
            product.category_id = data['category_id']
        if 'price' in data:
            product.selling_price = data['price']
        if 'cost_price' in data:
            product.cost_price = data['cost_price']
        if 'stock_quantity' in data:
            product.quantity = data['stock_quantity']
        if 'min_stock' in data:
            product.min_stock = data['min_stock']
        if 'is_active' in data:
            product.is_active = data['is_active']

        db.session.commit()

        return api_response(True, data=product.to_dict(), message='تم تحديث المنتج بنجاح')

    except Exception as e:
        db.session.rollback()
        return api_response(False, error=str(e), status_code=500)


@api_bp.route('/products/<int:id>', methods=['DELETE'])
@api_key_required
def delete_product(id):
    """حذف منتج"""
    product = Product.query.get(id)

    if not product:
        return api_response(False, error='المنتج غير موجود', status_code=404)

    try:
        # حذف ناعم
        product.is_active = False
        db.session.commit()

        return api_response(True, message='تم حذف المنتج بنجاح')

    except Exception as e:
        db.session.rollback()
        return api_response(False, error=str(e), status_code=500)


# =============== التصنيفات (Categories) ===============

@api_bp.route('/categories', methods=['GET'])
@api_key_required
def get_categories():
    """جلب جميع التصنيفات"""
    categories = Category.query.filter_by(
        is_active=True).order_by(Category.sort_order).all()

    return jsonify({
        'success': True,
        'data': [c.to_dict() for c in categories]
    })


@api_bp.route('/categories/<int:id>', methods=['GET'])
@api_key_required
def get_category(id):
    """جلب تصنيف بالـ ID"""
    category = Category.query.get(id)

    if not category:
        return api_response(False, error='التصنيف غير موجود', status_code=404)

    return api_response(True, data=category.to_dict())


@api_bp.route('/categories', methods=['POST'])
@api_key_required
def create_category():
    """إضافة تصنيف جديد"""
    data = request.get_json()

    if not data or 'name' not in data:
        return api_response(False, error='اسم التصنيف مطلوب', status_code=400)

    try:
        category = Category(
            name=data['name'],
            description=data.get('description'),
            icon=data.get('icon', 'category'),
            color=data.get('color', '#1e88e5'),
            sort_order=data.get('sort_order', 0),
            is_active=data.get('is_active', True)
        )

        db.session.add(category)
        db.session.commit()

        return api_response(True, data=category.to_dict(), message='تم إضافة التصنيف بنجاح', status_code=201)

    except Exception as e:
        db.session.rollback()
        return api_response(False, error=str(e), status_code=500)


@api_bp.route('/categories/<int:id>', methods=['PUT'])
@api_key_required
def update_category(id):
    """تحديث تصنيف"""
    category = Category.query.get(id)

    if not category:
        return api_response(False, error='التصنيف غير موجود', status_code=404)

    data = request.get_json()

    if not data:
        return api_response(False, error='بيانات غير صالحة', status_code=400)

    try:
        if 'name' in data:
            category.name = data['name']
        if 'description' in data:
            category.description = data['description']
        if 'icon' in data:
            category.icon = data['icon']
        if 'color' in data:
            category.color = data['color']
        if 'sort_order' in data:
            category.sort_order = data['sort_order']
        if 'is_active' in data:
            category.is_active = data['is_active']

        db.session.commit()

        return api_response(True, data=category.to_dict(), message='تم تحديث التصنيف بنجاح')

    except Exception as e:
        db.session.rollback()
        return api_response(False, error=str(e), status_code=500)


@api_bp.route('/categories/<int:id>', methods=['DELETE'])
@api_key_required
def delete_category(id):
    """حذف تصنيف"""
    category = Category.query.get(id)

    if not category:
        return api_response(False, error='التصنيف غير موجود', status_code=404)

    try:
        category.is_active = False
        db.session.commit()

        return api_response(True, message='تم حذف التصنيف بنجاح')

    except Exception as e:
        db.session.rollback()
        return api_response(False, error=str(e), status_code=500)


# =============== العملاء (Customers) ===============

@api_bp.route('/customers', methods=['GET'])
@api_key_required
def get_customers():
    """جلب جميع العملاء"""
    page = request.args.get('page', 1, type=int)
    per_page = min(100, request.args.get('per_page', 20, type=int))
    search = request.args.get('q', '')

    query = Customer.query.filter_by(is_active=True)

    if search:
        search_term = f'%{search}%'
        query = query.filter(
            db.or_(
                Customer.full_name.ilike(search_term),
                Customer.phone.ilike(search_term)
            )
        )

    total = query.count()
    customers = query.offset((page - 1) * per_page).limit(per_page).all()

    return jsonify({
        'success': True,
        'data': [c.to_dict() for c in customers],
        'pagination': {
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        }
    })


@api_bp.route('/customers/<int:id>', methods=['GET'])
@api_key_required
def get_customer(id):
    """جلب عميل بالـ ID"""
    customer = Customer.query.get(id)

    if not customer:
        return api_response(False, error='العميل غير موجود', status_code=404)

    return api_response(True, data=customer.to_dict())


@api_bp.route('/customers', methods=['POST'])
@api_key_required
def create_customer():
    """إضافة عميل جديد"""
    data = request.get_json()

    if not data:
        return api_response(False, error='بيانات غير صالحة', status_code=400)

    required_fields = ['full_name', 'phone']
    for field in required_fields:
        if field not in data:
            return api_response(False, error=f'الحقل {field} مطلوب', status_code=400)

    # التحقق من تكرار رقم الهاتف
    existing = Customer.query.filter_by(phone=data['phone']).first()
    if existing:
        return api_response(False, error='رقم الهاتف مسجل مسبقاً', status_code=400)

    try:
        customer = Customer(
            full_name=data['full_name'],
            phone=data['phone'],
            phone2=data.get('phone2'),
            national_id=data.get('national_id'),
            address=data.get('address'),
            work_address=data.get('work_address'),
            notes=data.get('notes'),
            is_active=data.get('is_active', True)
        )

        db.session.add(customer)
        db.session.commit()

        return api_response(True, data=customer.to_dict(), message='تم إضافة العميل بنجاح', status_code=201)

    except Exception as e:
        db.session.rollback()
        return api_response(False, error=str(e), status_code=500)


@api_bp.route('/customers/<int:id>', methods=['PUT'])
@api_key_required
def update_customer(id):
    """تحديث عميل"""
    customer = Customer.query.get(id)

    if not customer:
        return api_response(False, error='العميل غير موجود', status_code=404)

    data = request.get_json()

    if not data:
        return api_response(False, error='بيانات غير صالحة', status_code=400)

    try:
        if 'full_name' in data:
            customer.full_name = data['full_name']
        if 'phone' in data:
            # التحقق من تكرار رقم الهاتف
            existing = Customer.query.filter(
                Customer.phone == data['phone'],
                Customer.id != id
            ).first()
            if existing:
                return api_response(False, error='رقم الهاتف مسجل مسبقاً', status_code=400)
            customer.phone = data['phone']
        if 'phone2' in data:
            customer.phone2 = data['phone2']
        if 'national_id' in data:
            customer.national_id = data['national_id']
        if 'address' in data:
            customer.address = data['address']
        if 'work_address' in data:
            customer.work_address = data['work_address']
        if 'notes' in data:
            customer.notes = data['notes']
        if 'is_active' in data:
            customer.is_active = data['is_active']

        db.session.commit()

        return api_response(True, data=customer.to_dict(), message='تم تحديث العميل بنجاح')

    except Exception as e:
        db.session.rollback()
        return api_response(False, error=str(e), status_code=500)


@api_bp.route('/customers/<int:id>', methods=['DELETE'])
@api_key_required
def delete_customer(id):
    """حذف عميل"""
    customer = Customer.query.get(id)

    if not customer:
        return api_response(False, error='العميل غير موجود', status_code=404)

    try:
        customer.is_active = False
        db.session.commit()

        return api_response(True, message='تم حذف العميل بنجاح')

    except Exception as e:
        db.session.rollback()
        return api_response(False, error=str(e), status_code=500)


# =============== الفواتير (Invoices) ===============

@api_bp.route('/invoices', methods=['GET'])
@api_key_required
def get_invoices():
    """جلب جميع الفواتير"""
    page = request.args.get('page', 1, type=int)
    per_page = min(100, request.args.get('per_page', 20, type=int))
    invoice_type = request.args.get('type', '')
    status = request.args.get('status', '')
    customer_id = request.args.get('customer_id', type=int)

    query = Invoice.query

    if invoice_type:
        query = query.filter(Invoice.invoice_type == invoice_type)

    if status:
        query = query.filter(Invoice.status == status)

    if customer_id:
        query = query.filter(Invoice.customer_id == customer_id)

    query = query.order_by(Invoice.id.desc())

    total = query.count()
    invoices = query.offset((page - 1) * per_page).limit(per_page).all()

    return jsonify({
        'success': True,
        'data': [i.to_dict() for i in invoices],
        'pagination': {
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        }
    })


@api_bp.route('/invoices/<int:id>', methods=['GET'])
@api_key_required
def get_invoice(id):
    """جلب فاتورة بالـ ID"""
    invoice = Invoice.query.get(id)

    if not invoice:
        return api_response(False, error='الفاتورة غير موجودة', status_code=404)

    return jsonify({
        'success': True,
        'data': invoice.to_dict(include_items=True, include_installments=True)
    })


@api_bp.route('/invoices', methods=['POST'])
@api_key_required
def create_invoice():
    """إنشاء فاتورة جديدة"""
    data = request.get_json()

    if not data:
        return api_response(False, error='بيانات غير صالحة', status_code=400)

    required_fields = ['items', 'invoice_type']
    for field in required_fields:
        if field not in data:
            return api_response(False, error=f'الحقل {field} مطلوب', status_code=400)

    if not data['items'] or len(data['items']) == 0:
        return api_response(False, error='يجب إضافة منتج واحد على الأقل', status_code=400)

    try:
        # إنشاء الفاتورة
        invoice = Invoice(
            invoice_number=Invoice.generate_invoice_number(),
            customer_id=data.get('customer_id'),
            invoice_type=data['invoice_type'],
            status='paid' if data['invoice_type'] == 'cash' else 'pending',
            discount=data.get('discount', 0),
            notes=data.get('notes')
        )

        db.session.add(invoice)
        db.session.flush()

        total_amount = 0

        # إضافة عناصر الفاتورة
        for item in data['items']:
            product = Product.query.get(item['product_id'])
            if not product:
                db.session.rollback()
                return api_response(False, error=f'المنتج {item["product_id"]} غير موجود', status_code=400)

            quantity = item.get('quantity', 1)
            price = item.get('price', float(product.selling_price))

            invoice_item = InvoiceItem(
                invoice_id=invoice.id,
                product_id=product.id,
                product_name=product.name,
                quantity=quantity,
                unit_price=price,
                total_price=price * quantity
            )

            db.session.add(invoice_item)
            total_amount += price * quantity

            # خصم من المخزون
            if product.quantity >= quantity:
                product.quantity -= quantity

        # تحديث إجمالي الفاتورة
        invoice.total_amount = total_amount - float(data.get('discount', 0))
        invoice.paid_amount = data.get(
            'paid_amount', 0) if data['invoice_type'] == 'installment' else invoice.total_amount

        # إنشاء أقساط إذا كانت فاتورة تقسيط
        if data['invoice_type'] == 'installment':
            months = data.get('installment_months', 12)
            monthly_amount = (invoice.total_amount -
                              float(invoice.paid_amount)) / months

            for i in range(1, months + 1):
                due_date = date.today()
                due_date = due_date.replace(
                    month=((due_date.month - 1 + i) % 12) + 1)
                if due_date.month <= date.today().month and i > 0:
                    due_date = due_date.replace(year=due_date.year + 1)

                installment = Installment(
                    invoice_id=invoice.id,
                    installment_number=i,
                    amount=monthly_amount,
                    remaining_amount=monthly_amount,
                    due_date=due_date,
                    status='pending'
                )
                db.session.add(installment)

        db.session.commit()

        return api_response(True, data=invoice.to_dict(include_items=True), message='تم إنشاء الفاتورة بنجاح', status_code=201)

    except Exception as e:
        db.session.rollback()
        return api_response(False, error=str(e), status_code=500)


# =============== الأقساط (Installments) ===============

@api_bp.route('/installments', methods=['GET'])
@api_key_required
def get_installments():
    """جلب جميع الأقساط"""
    page = request.args.get('page', 1, type=int)
    per_page = min(100, request.args.get('per_page', 20, type=int))
    status = request.args.get('status', '')
    invoice_id = request.args.get('invoice_id', type=int)

    query = Installment.query

    if status:
        query = query.filter(Installment.status == status)

    if invoice_id:
        query = query.filter(Installment.invoice_id == invoice_id)

    query = query.order_by(Installment.due_date)

    total = query.count()
    installments = query.offset((page - 1) * per_page).limit(per_page).all()

    return jsonify({
        'success': True,
        'data': [i.to_dict() for i in installments],
        'pagination': {
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        }
    })


@api_bp.route('/installments/<int:id>', methods=['GET'])
@api_key_required
def get_installment(id):
    """جلب قسط بالـ ID"""
    installment = Installment.query.get(id)

    if not installment:
        return api_response(False, error='القسط غير موجود', status_code=404)

    return api_response(True, data=installment.to_dict())


@api_bp.route('/installments/today', methods=['GET'])
@api_key_required
def get_today_installments():
    """أقساط اليوم"""
    installments = Installment.get_today()

    return jsonify({
        'success': True,
        'data': [i.to_dict() for i in installments],
        'count': len(installments)
    })


@api_bp.route('/installments/overdue', methods=['GET'])
@api_key_required
def get_overdue_installments():
    """الأقساط المتأخرة"""
    Installment.update_overdue_status()
    installments = Installment.get_overdue()

    total_overdue = sum(float(i.remaining_amount or i.amount)
                        for i in installments)

    return jsonify({
        'success': True,
        'data': [i.to_dict() for i in installments],
        'count': len(installments),
        'total_amount': total_overdue
    })


@api_bp.route('/installments/<int:id>/pay', methods=['POST'])
@api_key_required
def pay_installment(id):
    """تسجيل دفعة على قسط"""
    installment = Installment.query.get(id)

    if not installment:
        return api_response(False, error='القسط غير موجود', status_code=404)

    if installment.status == 'paid':
        return api_response(False, error='هذا القسط مدفوع بالكامل', status_code=400)

    data = request.get_json() or {}
    amount = data.get('amount', float(
        installment.remaining_amount or installment.amount))
    payment_method = data.get('payment_method', 'cash')

    try:
        # إنشاء الدفعة
        payment = Payment(
            invoice_id=installment.invoice_id,
            installment_id=installment.id,
            amount=amount,
            payment_method=payment_method,
            receipt_number=Payment.generate_receipt_number() if hasattr(
                Payment, 'generate_receipt_number') else f"REC-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            payment_date=datetime.now(),
            notes=data.get('notes')
        )

        db.session.add(payment)

        # تحديث القسط
        remaining = float(
            installment.remaining_amount or installment.amount) - amount
        installment.remaining_amount = max(0, remaining)

        if remaining <= 0:
            installment.status = 'paid'
            installment.paid_date = date.today()
        else:
            installment.status = 'partial'

        # تحديث الفاتورة
        invoice = installment.invoice
        invoice.paid_amount = float(invoice.paid_amount or 0) + amount

        if float(invoice.paid_amount) >= float(invoice.total_amount):
            invoice.status = 'paid'

        db.session.commit()

        return api_response(True, data={
            'payment': payment.to_dict(),
            'installment': installment.to_dict()
        }, message='تم تسجيل الدفعة بنجاح')

    except Exception as e:
        db.session.rollback()
        return api_response(False, error=str(e), status_code=500)


# =============== المدفوعات (Payments) ===============

@api_bp.route('/payments', methods=['GET'])
@api_key_required
def get_payments():
    """جلب المدفوعات"""
    page = request.args.get('page', 1, type=int)
    per_page = min(100, request.args.get('per_page', 20, type=int))

    query = Payment.query.order_by(Payment.payment_date.desc())

    total = query.count()
    payments = query.offset((page - 1) * per_page).limit(per_page).all()

    return jsonify({
        'success': True,
        'data': [p.to_dict() for p in payments],
        'pagination': {
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        }
    })


@api_bp.route('/payments/today', methods=['GET'])
@api_key_required
def get_today_payments():
    """مدفوعات اليوم"""
    payments = Payment.get_today()
    total = Payment.get_today_total()

    return jsonify({
        'success': True,
        'data': [p.to_dict() for p in payments],
        'total': total
    })


# =============== لوحة التحكم (Dashboard) ===============

@api_bp.route('/dashboard/stats', methods=['GET'])
@api_key_required
def get_dashboard_stats():
    """إحصائيات لوحة التحكم"""
    Installment.update_overdue_status()
    today = date.today()

    today_invoices = Invoice.query.filter(
        db.func.date(Invoice.created_at) == today,
        Invoice.status != 'cancelled'
    ).all()

    # إحصائيات عامة
    total_products = Product.query.filter_by(is_active=True).count()
    total_customers = Customer.query.filter_by(is_active=True).count()
    total_invoices = Invoice.query.count()

    # الأقساط المتأخرة
    overdue_installments = Installment.get_overdue()
    overdue_total = sum(float(i.remaining_amount or i.amount)
                        for i in overdue_installments)

    return jsonify({
        'success': True,
        'data': {
            'today': {
                'cash_count': len([i for i in today_invoices if i.invoice_type == 'cash']),
                'cash_total': sum(float(i.total_amount) for i in today_invoices if i.invoice_type == 'cash'),
                'installment_count': len([i for i in today_invoices if i.invoice_type == 'installment']),
                'installment_total': sum(float(i.total_amount) for i in today_invoices if i.invoice_type == 'installment'),
                'payments_total': Payment.get_today_total()
            },
            'totals': {
                'products': total_products,
                'customers': total_customers,
                'invoices': total_invoices
            },
            'installments': Installment.get_stats(),
            'overdue': {
                'count': len(overdue_installments),
                'total': overdue_total
            }
        }
    })


@api_bp.route('/dashboard/summary', methods=['GET'])
@api_key_required
def get_dashboard_summary():
    """ملخص لوحة التحكم"""
    period = request.args.get('period', 'month')  # day, week, month, year

    today = date.today()

    if period == 'day':
        start_date = today
    elif period == 'week':
        start_date = today.replace(day=today.day - today.weekday())
    elif period == 'year':
        start_date = today.replace(month=1, day=1)
    else:  # month
        start_date = today.replace(day=1)

    invoices = Invoice.query.filter(
        db.func.date(Invoice.created_at) >= start_date,
        Invoice.status != 'cancelled'
    ).all()

    payments = Payment.query.filter(
        db.func.date(Payment.payment_date) >= start_date
    ).all()

    return jsonify({
        'success': True,
        'data': {
            'period': period,
            'start_date': start_date.isoformat(),
            'end_date': today.isoformat(),
            'sales': {
                'count': len(invoices),
                'total': sum(float(i.total_amount) for i in invoices),
                'cash': sum(float(i.total_amount) for i in invoices if i.invoice_type == 'cash'),
                'installment': sum(float(i.total_amount) for i in invoices if i.invoice_type == 'installment')
            },
            'collections': {
                'count': len(payments),
                'total': sum(float(p.amount) for p in payments)
            }
        }
    })


# =============== البحث (Search) ===============

@api_bp.route('/search', methods=['GET'])
@api_key_required
def search():
    """بحث شامل"""
    q = request.args.get('q', '')

    if len(q) < 2:
        return api_response(False, error='يجب إدخال حرفين على الأقل للبحث', status_code=400)

    search_term = f'%{q}%'

    products = Product.query.filter(
        db.and_(
            Product.is_active == True,
            db.or_(
                Product.name.ilike(search_term),
                Product.barcode.ilike(search_term)
            )
        )
    ).limit(10).all()

    customers = Customer.query.filter(
        db.and_(
            Customer.is_active == True,
            db.or_(
                Customer.full_name.ilike(search_term),
                Customer.phone.ilike(search_term)
            )
        )
    ).limit(10).all()

    invoices = Invoice.query.filter(
        Invoice.invoice_number.ilike(search_term)
    ).limit(10).all()

    return jsonify({
        'success': True,
        'data': {
            'products': [p.to_dict() for p in products],
            'customers': [c.to_dict() for c in customers],
            'invoices': [i.to_dict() for i in invoices]
        }
    })
