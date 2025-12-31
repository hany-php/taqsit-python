"""
متحكم الأقساط
"""
from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.installment import Installment
from app.models.invoice import Invoice
from app.models.activity_log import ActivityLog

installments_bp = Blueprint('installments', __name__)


@installments_bp.route('/')
@login_required
def index():
    """قائمة الأقساط (عقود التقسيط)"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('q', '')
    status = request.args.get('status', '')

    query = Invoice.query.filter_by(invoice_type='installment')

    if search:
        from app.models.customer import Customer
        search_term = f'%{search}%'
        query = query.join(Customer, isouter=True).filter(
            db.or_(
                Invoice.invoice_number.ilike(search_term),
                Customer.full_name.ilike(search_term)
            )
        )

    if status:
        query = query.filter(Invoice.status == status)

    query = query.order_by(Invoice.id.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    invoices = pagination.items

    return render_template('installments/index.html',
                           page_title='عقود التقسيط',
                           invoices=invoices,
                           pagination=pagination,
                           search=search,
                           status=status
                           )


@installments_bp.route('/today')
@login_required
def today():
    """أقساط اليوم"""
    installments = Installment.get_today()

    return render_template('installments/today.html',
                           page_title='أقساط اليوم',
                           installments=installments
                           )


@installments_bp.route('/overdue')
@login_required
def overdue():
    """الأقساط المتأخرة"""
    # تحديث حالات الأقساط المتأخرة
    Installment.update_overdue_status()

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    query = Installment.query.filter(
        Installment.due_date < date.today(),
        Installment.status.in_(['pending', 'partial', 'overdue'])
    ).order_by(Installment.due_date)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    installments = pagination.items

    # حساب الإجمالي
    total_overdue = db.session.query(
        db.func.coalesce(db.func.sum(Installment.remaining_amount), 0)
    ).filter(
        Installment.due_date < date.today(),
        Installment.status.in_(['pending', 'partial', 'overdue'])
    ).scalar()

    return render_template('installments/overdue.html',
                           page_title='الأقساط المتأخرة',
                           installments=installments,
                           pagination=pagination,
                           total_overdue=float(
                               total_overdue) if total_overdue else 0
                           )


@installments_bp.route('/<int:id>/pay', methods=['POST'])
@login_required
def pay(id):
    """دفع قسط"""
    installment = Installment.query.get_or_404(id)

    if installment.status == 'paid':
        return jsonify({'success': False, 'message': 'هذا القسط مدفوع بالكامل'})

    amount = request.form.get('amount', type=float)

    if not amount or amount <= 0:
        return jsonify({'success': False, 'message': 'المبلغ غير صالح'})

    remaining = float(installment.remaining_amount or installment.amount)

    if amount > remaining:
        return jsonify({'success': False, 'message': f'المبلغ أكبر من المتبقي ({remaining})'})

    notes = request.form.get('notes', '')

    # تنفيذ الدفع
    payment = installment.pay(amount, user_id=current_user.id, notes=notes)

    ActivityLog.log(
        user_id=current_user.id,
        action='pay',
        entity_type='installment',
        entity_id=installment.id,
        description=f'دفع قسط: {amount} للفاتورة {installment.invoice.invoice_number}',
        ip_address=request.remote_addr
    )

    return jsonify({
        'success': True,
        'message': 'تم تسجيل الدفعة بنجاح',
        'receipt_number': payment.receipt_number,
        'new_status': installment.status,
        'remaining': float(installment.remaining_amount)
    })


@installments_bp.route('/calendar')
@login_required
def calendar():
    """تقويم الأقساط"""
    month = request.args.get('month', date.today().month, type=int)
    year = request.args.get('year', date.today().year, type=int)

    # جلب الأقساط للشهر
    from datetime import timedelta
    from calendar import monthrange

    _, days_in_month = monthrange(year, month)
    start_date = date(year, month, 1)
    end_date = date(year, month, days_in_month)

    installments = Installment.query.filter(
        Installment.due_date >= start_date,
        Installment.due_date <= end_date,
        Installment.status.in_(['pending', 'partial', 'overdue'])
    ).order_by(Installment.due_date).all()

    # تجميع حسب اليوم
    calendar_data = {}
    for inst in installments:
        day = inst.due_date.day
        if day not in calendar_data:
            calendar_data[day] = []
        calendar_data[day].append(inst)

    return render_template('installments/calendar.html',
                           page_title='تقويم الأقساط',
                           installments=installments,
                           calendar_data=calendar_data,
                           month=month,
                           year=year,
                           days_in_month=days_in_month
                           )
