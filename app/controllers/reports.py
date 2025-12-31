"""
متحكم التقارير
"""
from datetime import date, datetime
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.invoice import Invoice, InvoiceItem
from app.models.payment import Payment
from app.models.product import Product
from app.models.installment import Installment
from app.utils.decorators import admin_required

reports_bp = Blueprint('reports', __name__)


def parse_date(date_str):
    """تحويل نص التاريخ إلى date object"""
    if not date_str:
        return None
    return datetime.strptime(date_str, '%Y-%m-%d').date()


@reports_bp.route('/')
@login_required
def index():
    """صفحة التقارير"""
    return render_template('reports/index.html',
                           page_title='التقارير'
                           )


@reports_bp.route('/profits')
@admin_required
def profits():
    """تقرير الأرباح"""
    from_date_str = request.args.get(
        'from', date.today().replace(day=1).isoformat())
    to_date_str = request.args.get('to', date.today().isoformat())
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    from_date = parse_date(from_date_str)
    to_date = parse_date(to_date_str)

    # جلب الفواتير المكتملة
    query = db.session.query(
        InvoiceItem.product_id,
        InvoiceItem.product_name,
        db.func.sum(InvoiceItem.quantity).label('total_qty'),
        db.func.sum(InvoiceItem.total_price).label('revenue'),
        Product.cost_price
    ).join(Invoice).outerjoin(
        Product, InvoiceItem.product_id == Product.id
    ).filter(
        db.func.date(Invoice.created_at) >= from_date,
        db.func.date(Invoice.created_at) <= to_date,
        Invoice.status != 'cancelled'
    ).group_by(
        InvoiceItem.product_id,
        InvoiceItem.product_name,
        Product.cost_price
    )

    # الحصول على جميع النتائج لحساب الإجماليات
    all_results = query.all()

    # حساب الإجماليات من جميع البيانات
    total_revenue = 0
    total_cost = 0
    total_profit = 0

    for r in all_results:
        revenue = float(r.revenue or 0)
        cost = float(r.cost_price or 0) * float(r.total_qty)
        profit = revenue - cost
        total_revenue += revenue
        total_cost += cost
        total_profit += profit

    # Pagination يدوي
    total_items = len(all_results)
    total_pages = (total_items + per_page - 1) // per_page
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    page_results = all_results[start_idx:end_idx]

    # حساب الأرباح للصفحة الحالية
    profits = []
    for r in page_results:
        revenue = float(r.revenue or 0)
        cost = float(r.cost_price or 0) * float(r.total_qty)
        profit = revenue - cost

        profits.append({
            'product_name': r.product_name,
            'quantity': r.total_qty,
            'revenue': revenue,
            'cost': cost,
            'profit': profit
        })

    # إنشاء كائن pagination مخصص
    class Pagination:
        def __init__(self, page, per_page, total, items):
            self.page = page
            self.per_page = per_page
            self.total = total
            self.items = items
            self.pages = (total + per_page - 1) // per_page if total > 0 else 1
            self.has_prev = page > 1
            self.has_next = page < self.pages
            self.prev_num = page - 1 if self.has_prev else None
            self.next_num = page + 1 if self.has_next else None

        def iter_pages(self, left_edge=2, left_current=2, right_current=3, right_edge=2):
            last = 0
            for num in range(1, self.pages + 1):
                if num <= left_edge or \
                   (num >= self.page - left_current and num <= self.page + right_current) or \
                   num > self.pages - right_edge:
                    if last + 1 != num:
                        yield None
                    yield num
                    last = num

    pagination = Pagination(page, per_page, total_items, profits)

    return render_template('reports/profits.html',
                           page_title='تقرير الأرباح',
                           profits=profits,
                           pagination=pagination,
                           from_date=from_date_str,
                           to_date=to_date_str,
                           total_revenue=total_revenue,
                           total_cost=total_cost,
                           total_profit=total_profit
                           )


@reports_bp.route('/sales')
@login_required
def sales():
    """تقرير المبيعات"""
    from_date_str = request.args.get(
        'from', date.today().replace(day=1).isoformat())
    to_date_str = request.args.get('to', date.today().isoformat())

    from_date = parse_date(from_date_str)
    to_date = parse_date(to_date_str)

    # إحصائيات المبيعات
    invoices = Invoice.query.filter(
        db.func.date(Invoice.created_at) >= from_date,
        db.func.date(Invoice.created_at) <= to_date,
        Invoice.status != 'cancelled'
    ).all()

    cash_total = sum(float(i.total_amount)
                     for i in invoices if i.invoice_type == 'cash')
    installment_total = sum(float(i.total_amount)
                            for i in invoices if i.invoice_type == 'installment')

    # المبيعات اليومية
    daily_sales = db.session.query(
        db.func.date(Invoice.created_at).label('date'),
        db.func.sum(Invoice.total_amount).label('total')
    ).filter(
        db.func.date(Invoice.created_at) >= from_date,
        db.func.date(Invoice.created_at) <= to_date,
        Invoice.status != 'cancelled'
    ).group_by(
        db.func.date(Invoice.created_at)
    ).order_by('date').all()

    return render_template('reports/sales.html',
                           page_title='تقرير المبيعات',
                           invoices=invoices,
                           cash_total=cash_total,
                           installment_total=installment_total,
                           daily_sales=daily_sales,
                           from_date=from_date_str,
                           to_date=to_date_str
                           )


@reports_bp.route('/collections')
@login_required
def collections():
    """تقرير التحصيل"""
    from_date_str = request.args.get(
        'from', date.today().replace(day=1).isoformat())
    to_date_str = request.args.get('to', date.today().isoformat())

    from_date = parse_date(from_date_str)
    to_date = parse_date(to_date_str)

    payments = Payment.get_by_date_range(from_date, to_date)
    total = Payment.get_total_by_date_range(from_date, to_date)

    # التحصيل اليومي
    daily_collections = db.session.query(
        db.func.date(Payment.payment_date).label('date'),
        db.func.sum(Payment.amount).label('total')
    ).filter(
        db.func.date(Payment.payment_date) >= from_date,
        db.func.date(Payment.payment_date) <= to_date
    ).group_by(
        db.func.date(Payment.payment_date)
    ).order_by('date').all()

    return render_template('reports/collections.html',
                           page_title='تقرير التحصيل',
                           payments=payments,
                           total=total,
                           daily_collections=daily_collections,
                           from_date=from_date_str,
                           to_date=to_date_str
                           )


@reports_bp.route('/overdue')
@login_required
def overdue():
    """تقرير الأقساط المتأخرة"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    # تحديث حالات الأقساط المتأخرة
    Installment.update_overdue_status()

    installments = Installment.get_overdue()

    # تجميع حسب العميل
    customers_data = {}
    for inst in installments:
        customer = inst.invoice.customer
        if customer:
            if customer.id not in customers_data:
                customers_data[customer.id] = {
                    'customer': customer,
                    'installments': [],
                    'total': 0
                }
            customers_data[customer.id]['installments'].append(inst)
            customers_data[customer.id]['total'] += float(
                inst.remaining_amount or inst.amount)

    total_overdue = sum(c['total'] for c in customers_data.values())
    all_customers = list(customers_data.values())

    # Pagination يدوي
    total_items = len(all_customers)
    total_pages = (total_items + per_page -
                   1) // per_page if total_items > 0 else 1
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    page_customers = all_customers[start_idx:end_idx]

    # إنشاء كائن pagination مخصص
    class Pagination:
        def __init__(self, p, pp, total, items):
            self.page = p
            self.per_page = pp
            self.total = total
            self.items = items
            self.pages = (total + pp - 1) // pp if total > 0 else 1
            self.has_prev = p > 1
            self.has_next = p < self.pages
            self.prev_num = p - 1 if self.has_prev else None
            self.next_num = p + 1 if self.has_next else None

        def iter_pages(self, left_edge=2, left_current=2, right_current=3, right_edge=2):
            last = 0
            for num in range(1, self.pages + 1):
                if num <= left_edge or \
                   (num >= self.page - left_current and num <= self.page + right_current) or \
                   num > self.pages - right_edge:
                    if last + 1 != num:
                        yield None
                    yield num
                    last = num

    pagination = Pagination(page, per_page, total_items, page_customers)

    return render_template('reports/overdue.html',
                           page_title='تقرير الأقساط المتأخرة',
                           customers_data=page_customers,
                           pagination=pagination,
                           total_customers=total_items,
                           total_overdue=total_overdue
                           )


@reports_bp.route('/inventory')
@login_required
def inventory():
    """تقرير المخزون"""
    products = Product.query.filter_by(
        is_active=True).order_by(Product.name).all()

    low_stock = [p for p in products if p.is_low_stock]
    total_value = sum(float(p.cost_price or 0) * p.quantity for p in products)

    return render_template('reports/inventory.html',
                           page_title='تقرير المخزون',
                           products=products,
                           low_stock=low_stock,
                           total_value=total_value
                           )
