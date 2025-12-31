"""
متحكم لوحة التحكم
"""
from datetime import date
from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.invoice import Invoice
from app.models.installment import Installment
from app.models.payment import Payment
from app.models.product import Product
from app.models.customer import Customer

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/dashboard')
@login_required
def index():
    """لوحة التحكم الرئيسية"""
    # تحديث حالات الأقساط المتأخرة
    Installment.update_overdue_status()

    today = date.today()

    # إحصائيات اليوم
    today_invoices = Invoice.query.filter(
        db.func.date(Invoice.created_at) == today,
        Invoice.status != 'cancelled'
    ).all()

    today_stats = {
        'cash_count': len([i for i in today_invoices if i.invoice_type == 'cash']),
        'cash_total': sum(float(i.total_amount) for i in today_invoices if i.invoice_type == 'cash'),
        'installment_count': len([i for i in today_invoices if i.invoice_type == 'installment']),
        'installment_total': sum(float(i.total_amount) for i in today_invoices if i.invoice_type == 'installment'),
    }

    # إحصائيات المدفوعات
    today_payments = Payment.get_today_total()

    # إحصائيات الأقساط
    installment_stats = Installment.get_stats()

    # إحصائيات عامة
    stats = {
        'products_count': Product.query.filter_by(is_active=True).count(),
        'customers_count': Customer.query.count(),
        'low_stock_count': len(Product.get_low_stock()),
        'active_installments': Invoice.query.filter_by(
            invoice_type='installment',
            status='active'
        ).count(),
    }

    # أقساط اليوم
    today_installments = Installment.get_today()

    # الأقساط المتأخرة
    overdue_installments = Installment.get_overdue()[:5]

    # آخر الفواتير
    recent_invoices = Invoice.query.order_by(Invoice.id.desc()).limit(5).all()

    # آخر المدفوعات
    recent_payments = Payment.get_today()[:5]

    return render_template('dashboard/index.html',
                           page_title='لوحة التحكم',
                           today_stats=today_stats,
                           today_payments=today_payments,
                           installment_stats=installment_stats,
                           stats=stats,
                           today_installments=today_installments,
                           overdue_installments=overdue_installments,
                           recent_invoices=recent_invoices,
                           recent_payments=recent_payments,
                           )


@dashboard_bp.route('/dashboard/stats')
@login_required
def stats():
    """إحصائيات AJAX"""
    today = date.today()

    today_invoices = Invoice.query.filter(
        db.func.date(Invoice.created_at) == today,
        Invoice.status != 'cancelled'
    ).all()

    return jsonify({
        'today': {
            'cash_count': len([i for i in today_invoices if i.invoice_type == 'cash']),
            'cash_total': sum(float(i.total_amount) for i in today_invoices if i.invoice_type == 'cash'),
            'installment_count': len([i for i in today_invoices if i.invoice_type == 'installment']),
            'installment_total': sum(float(i.total_amount) for i in today_invoices if i.invoice_type == 'installment'),
        },
        'installments': Installment.get_stats(),
        'payments': Payment.get_today_total()
    })
