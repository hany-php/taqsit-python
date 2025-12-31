"""
متحكم الفواتير
"""
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.invoice import Invoice, InvoiceItem
from app.models.installment import Installment
from app.models.payment import Payment
from app.models.product import Product
from app.models.customer import Customer
from app.models.activity_log import ActivityLog
from app.utils.decorators import admin_required

invoices_bp = Blueprint('invoices', __name__)


@invoices_bp.route('/')
@login_required
def index():
    """قائمة الفواتير"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('q', '')
    filter_type = request.args.get('type', '')
    status = request.args.get('status', '')

    query = Invoice.query

    if search:
        search_term = f'%{search}%'
        query = query.join(Customer, isouter=True).filter(
            db.or_(
                Invoice.invoice_number.ilike(search_term),
                Customer.full_name.ilike(search_term)
            )
        )

    if filter_type:
        query = query.filter(Invoice.invoice_type == filter_type)

    if status:
        query = query.filter(Invoice.status == status)

    query = query.order_by(Invoice.id.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    invoices = pagination.items

    return render_template('invoices/index.html',
                           page_title='إدارة الفواتير',
                           invoices=invoices,
                           pagination=pagination,
                           search=search,
                           filter_type=filter_type,
                           status=status
                           )


@invoices_bp.route('/<int:id>')
@login_required
def show(id):
    """عرض فاتورة"""
    invoice = Invoice.query.get_or_404(id)
    return render_template('invoices/show.html',
                           page_title=f'الفاتورة: {invoice.invoice_number}',
                           invoice=invoice
                           )


@invoices_bp.route('/pos')
@login_required
def pos():
    """نقطة البيع - فاتورة نقدية"""
    from app.models.category import Category

    products = Product.get_active()
    customers = Customer.query.filter_by(
        is_active=True).order_by(Customer.full_name).all()
    categories = Category.query.filter_by(
        is_active=True).order_by(Category.name).all()
    new_customer_id = request.args.get('new_customer_id', type=int)

    return render_template('pos/index.html',
                           page_title='نقطة البيع',
                           products=products,
                           customers=customers,
                           categories=categories,
                           new_customer_id=new_customer_id
                           )


@invoices_bp.route('/pos/installment')
@login_required
def pos_installment():
    """نقطة البيع - فاتورة تقسيط"""
    products = Product.get_active()
    customers = Customer.query.filter_by(
        is_active=True).order_by(Customer.full_name).all()
    new_customer_id = request.args.get('new_customer_id', type=int)

    return render_template('pos/installment.html',
                           page_title='بيع بالتقسيط',
                           products=products,
                           customers=customers,
                           new_customer_id=new_customer_id
                           )


@invoices_bp.route('/store', methods=['POST'])
@login_required
def store():
    """إنشاء فاتورة"""
    try:
        invoice_type = request.form.get('invoice_type', 'cash')
        customer_id = request.form.get('customer_id', type=int)
        items_data = request.form.getlist('items[]')

        # حساب الإجمالي
        total_amount = 0
        items = []

        # معالجة البنود
        product_ids = request.form.getlist('product_id[]')
        quantities = request.form.getlist('quantity[]')
        prices = request.form.getlist('price[]')

        for i, product_id in enumerate(product_ids):
            product = Product.query.get(product_id)
            if not product:
                continue

            qty = int(quantities[i]) if i < len(quantities) else 1
            price = float(prices[i]) if i < len(
                prices) else float(product.cash_price)
            total = qty * price
            total_amount += total

            items.append({
                'product_id': product.id,
                'product_name': product.name,
                'quantity': qty,
                'unit_price': price,
                'total_price': total
            })

            # تقليل الكمية
            product.quantity -= qty

        if not items:
            return jsonify({'success': False, 'message': 'يجب إضافة منتج واحد على الأقل'})

        # إنشاء الفاتورة
        invoice = Invoice(
            invoice_number=Invoice.generate_invoice_number(),
            customer_id=customer_id if customer_id else None,
            user_id=current_user.id,
            invoice_type=invoice_type,
            total_amount=total_amount,
            notes=request.form.get('notes')
        )

        if invoice_type == 'cash':
            invoice.paid_amount = total_amount
            invoice.remaining_amount = 0
            invoice.status = 'completed'
        else:
            # فاتورة تقسيط
            down_payment = request.form.get('down_payment', 0, type=float)
            installment_months = request.form.get(
                'installment_months', 12, type=int)

            remaining = total_amount - down_payment
            monthly = remaining / installment_months if installment_months > 0 else remaining

            invoice.down_payment = down_payment
            invoice.paid_amount = down_payment
            invoice.remaining_amount = remaining
            invoice.monthly_installment = monthly
            invoice.installment_months = installment_months
            invoice.status = 'active'

        db.session.add(invoice)
        db.session.flush()  # للحصول على ID

        # إضافة البنود
        for item in items:
            invoice_item = InvoiceItem(
                invoice_id=invoice.id,
                **item
            )
            db.session.add(invoice_item)

        # إنشاء الأقساط للفاتورة التقسيط
        if invoice_type == 'installment':
            for i in range(installment_months):
                due_date = date.today() + relativedelta(months=i+1)
                installment = Installment(
                    invoice_id=invoice.id,
                    installment_number=i + 1,
                    amount=monthly,
                    remaining_amount=monthly,
                    due_date=due_date,
                    status='pending'
                )
                db.session.add(installment)

            # تسجيل الدفعة المقدمة
            if down_payment > 0:
                receipt_number = f"RCP-{datetime.utcnow().strftime('%Y%m%d')}-{Payment.query.count():04d}"
                payment = Payment(
                    invoice_id=invoice.id,
                    amount=down_payment,
                    payment_method='cash',
                    receipt_number=receipt_number,
                    user_id=current_user.id,
                    notes='دفعة مقدمة'
                )
                db.session.add(payment)
        else:
            # دفعة للفاتورة النقدية
            receipt_number = f"RCP-{datetime.utcnow().strftime('%Y%m%d')}-{Payment.query.count():04d}"
            payment = Payment(
                invoice_id=invoice.id,
                amount=total_amount,
                payment_method='cash',
                receipt_number=receipt_number,
                user_id=current_user.id,
                notes='دفع نقدي كامل'
            )
            db.session.add(payment)

        db.session.commit()

        ActivityLog.log(
            user_id=current_user.id,
            action='create',
            entity_type='invoice',
            entity_id=invoice.id,
            description=f'إنشاء فاتورة: {invoice.invoice_number}',
            ip_address=request.remote_addr
        )

        return jsonify({
            'success': True,
            'message': 'تم إنشاء الفاتورة بنجاح',
            'invoice_id': invoice.id,
            'invoice_number': invoice.invoice_number
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


@invoices_bp.route('/<int:id>/print')
@login_required
def print_invoice(id):
    """طباعة الفاتورة"""
    invoice = Invoice.query.get_or_404(id)
    return render_template('invoices/print.html',
                           invoice=invoice
                           )


@invoices_bp.route('/<int:id>/cancel', methods=['POST'])
@admin_required
def cancel(id):
    """إلغاء فاتورة"""
    invoice = Invoice.query.get_or_404(id)

    if invoice.status == 'cancelled':
        return jsonify({'success': False, 'message': 'الفاتورة ملغاة مسبقاً'})

    # إرجاع الكميات
    for item in invoice.items:
        if item.product:
            item.product.quantity += item.quantity

    invoice.status = 'cancelled'
    db.session.commit()

    ActivityLog.log(
        user_id=current_user.id,
        action='cancel',
        entity_type='invoice',
        entity_id=invoice.id,
        description=f'إلغاء فاتورة: {invoice.invoice_number}',
        ip_address=request.remote_addr
    )

    return jsonify({'success': True, 'message': 'تم إلغاء الفاتورة بنجاح'})
