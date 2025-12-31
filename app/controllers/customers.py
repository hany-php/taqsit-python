"""
متحكم العملاء
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.customer import Customer
from app.models.activity_log import ActivityLog
from app.utils.decorators import admin_required

customers_bp = Blueprint('customers', __name__)


@customers_bp.route('/')
@login_required
def index():
    """قائمة العملاء"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('q', '')

    query = Customer.query

    if search:
        search_term = f'%{search}%'
        query = query.filter(
            db.or_(
                Customer.full_name.ilike(search_term),
                Customer.phone.ilike(search_term),
                Customer.national_id.ilike(search_term)
            )
        )

    query = query.order_by(Customer.id.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    customers = pagination.items

    return render_template('customers/index.html',
                           page_title='إدارة العملاء',
                           customers=customers,
                           pagination=pagination,
                           search=search
                           )


@customers_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """إضافة عميل"""
    if request.method == 'POST':
        customer = Customer(
            full_name=request.form.get('full_name'),
            phone=request.form.get('phone'),
            phone2=request.form.get('phone2'),
            national_id=request.form.get('national_id'),
            address=request.form.get('address'),
            city=request.form.get('city'),
            work_address=request.form.get('work_address'),
            work_phone=request.form.get('work_phone'),
            guarantor_name=request.form.get('guarantor_name'),
            guarantor_phone=request.form.get('guarantor_phone'),
            guarantor_national_id=request.form.get('guarantor_national_id'),
            credit_limit=request.form.get('credit_limit', 0, type=float),
            notes=request.form.get('notes'),
            is_active=True
        )

        db.session.add(customer)
        db.session.commit()

        ActivityLog.log(
            user_id=current_user.id,
            action='create',
            entity_type='customer',
            entity_id=customer.id,
            description=f'إضافة عميل: {customer.full_name}',
            ip_address=request.remote_addr
        )

        flash('تم إضافة العميل بنجاح', 'success')

        return_to = request.form.get('return_to')
        if return_to == 'pos':
            return redirect(url_for('invoices.pos', new_customer_id=customer.id))

        return redirect(url_for('customers.index'))

    return render_template('customers/create.html',
                           page_title='إضافة عميل جديد'
                           )


@customers_bp.route('/store-ajax', methods=['POST'])
@login_required
def store_ajax():
    """إضافة عميل (AJAX)"""
    try:
        full_name = request.form.get('full_name')
        phone = request.form.get('phone')

        if not full_name or not phone:
            return jsonify({'success': False, 'message': 'الاسم ورقم الهاتف مطلوبان'})

        customer = Customer(
            full_name=full_name,
            phone=phone,
            phone2=request.form.get('phone2'),
            national_id=request.form.get('national_id'),
            address=request.form.get('address'),
            credit_limit=request.form.get('credit_limit', 5000, type=float),
            is_active=True
        )

        db.session.add(customer)
        db.session.commit()

        ActivityLog.log(
            user_id=current_user.id,
            action='create',
            entity_type='customer',
            entity_id=customer.id,
            description=f'إضافة عميل (POS): {customer.full_name}',
            ip_address=request.remote_addr
        )

        return jsonify({
            'success': True,
            'customer': {
                'id': customer.id,
                'full_name': customer.full_name,
                'phone': customer.phone
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@customers_bp.route('/<int:id>')
@login_required
def show(id):
    """عرض عميل"""
    customer = Customer.query.get_or_404(id)
    invoices = customer.get_invoices()
    payments = customer.get_payments()

    return render_template('customers/show.html',
                           page_title=f'ملف العميل: {customer.full_name}',
                           customer=customer,
                           invoices=invoices,
                           payments=payments,
                           balance=customer.balance
                           )


@customers_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """تعديل عميل"""
    customer = Customer.query.get_or_404(id)

    if request.method == 'POST':
        customer.full_name = request.form.get('full_name')
        customer.phone = request.form.get('phone')
        customer.phone2 = request.form.get('phone2')
        customer.national_id = request.form.get('national_id')
        customer.address = request.form.get('address')
        customer.city = request.form.get('city')
        customer.work_address = request.form.get('work_address')
        customer.work_phone = request.form.get('work_phone')
        customer.guarantor_name = request.form.get('guarantor_name')
        customer.guarantor_phone = request.form.get('guarantor_phone')
        customer.guarantor_national_id = request.form.get(
            'guarantor_national_id')
        customer.credit_limit = request.form.get('credit_limit', 0, type=float)
        customer.notes = request.form.get('notes')
        customer.is_active = bool(request.form.get('is_active'))

        db.session.commit()

        ActivityLog.log(
            user_id=current_user.id,
            action='update',
            entity_type='customer',
            entity_id=customer.id,
            description=f'تعديل عميل: {customer.full_name}',
            ip_address=request.remote_addr
        )

        flash('تم تحديث بيانات العميل بنجاح', 'success')
        return redirect(url_for('customers.index'))

    return render_template('customers/edit.html',
                           page_title=f'تعديل: {customer.full_name}',
                           customer=customer
                           )


@customers_bp.route('/<int:id>/delete', methods=['POST'])
@admin_required
def delete(id):
    """حذف عميل"""
    customer = Customer.query.get_or_404(id)

    if customer.invoices.count() > 0:
        if request.is_json:
            return jsonify({'success': False, 'message': 'لا يمكن حذف العميل لوجود فواتير مرتبطة'})
        flash('لا يمكن حذف العميل لوجود فواتير مرتبطة', 'error')
        return redirect(url_for('customers.index'))

    name = customer.full_name
    db.session.delete(customer)
    db.session.commit()

    ActivityLog.log(
        user_id=current_user.id,
        action='delete',
        entity_type='customer',
        entity_id=id,
        description=f'حذف عميل: {name}',
        ip_address=request.remote_addr
    )

    if request.is_json:
        return jsonify({'success': True, 'message': 'تم حذف العميل بنجاح'})

    flash('تم حذف العميل بنجاح', 'success')
    return redirect(url_for('customers.index'))


@customers_bp.route('/search')
@login_required
def search():
    """بحث في العملاء (API)"""
    q = request.args.get('q', '')
    customers = Customer.search(q)
    return jsonify([c.to_dict() for c in customers])
