"""
متحكم المدفوعات
"""
from datetime import date, datetime
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.payment import Payment
from app.models.invoice import Invoice
from app.models.activity_log import ActivityLog

payments_bp = Blueprint('payments', __name__)


@payments_bp.route('/')
@login_required
def index():
    """قائمة المدفوعات"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    from_date_str = request.args.get(
        'from', date.today().replace(day=1).isoformat())
    to_date_str = request.args.get('to', date.today().isoformat())

    # تحويل النصوص إلى تواريخ
    from_date = datetime.strptime(
        from_date_str, '%Y-%m-%d').date() if from_date_str else None
    to_date = datetime.strptime(
        to_date_str, '%Y-%m-%d').date() if to_date_str else None

    query = Payment.query

    if from_date:
        query = query.filter(db.func.date(Payment.payment_date) >= from_date)

    if to_date:
        query = query.filter(db.func.date(Payment.payment_date) <= to_date)

    query = query.order_by(Payment.payment_date.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    payments = pagination.items

    # حساب الإجماليات
    total = Payment.get_total_by_date_range(from_date, to_date)

    return render_template('payments/index.html',
                           page_title='سجل المدفوعات',
                           payments=payments,
                           pagination=pagination,
                           from_date=from_date_str,
                           to_date=to_date_str,
                           total=total
                           )


@payments_bp.route('/today')
@login_required
def today():
    """مدفوعات اليوم"""
    payments = Payment.get_today()
    total = Payment.get_today_total()

    return render_template('payments/today.html',
                           page_title='مدفوعات اليوم',
                           payments=payments,
                           total=total
                           )


@payments_bp.route('/receipt/<int:id>')
@login_required
def receipt(id):
    """عرض الإيصال"""
    payment = Payment.query.get_or_404(id)

    return render_template('payments/receipt.html',
                           page_title=f'إيصال: {payment.receipt_number}',
                           payment=payment
                           )


@payments_bp.route('/receipt/<int:id>/print')
@login_required
def print_receipt(id):
    """طباعة الإيصال"""
    payment = Payment.query.get_or_404(id)

    return render_template('payments/print_receipt.html',
                           payment=payment
                           )
