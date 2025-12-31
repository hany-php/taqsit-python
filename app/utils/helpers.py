"""
دوال مساعدة
"""
from datetime import datetime, date
from flask import current_app


def format_money(amount, currency=None):
    """تنسيق المبلغ المالي"""
    if amount is None:
        amount = 0

    if currency is None:
        currency = current_app.config.get('CURRENCY', 'ج.م')

    return f"{float(amount):,.2f} {currency}"


def format_date(dt):
    """تنسيق التاريخ"""
    if dt is None:
        return '-'

    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt)
        except:
            return dt

    if isinstance(dt, datetime):
        return dt.strftime('%Y-%m-%d')
    elif isinstance(dt, date):
        return dt.strftime('%Y-%m-%d')

    return str(dt)


def format_datetime(dt):
    """تنسيق التاريخ والوقت"""
    if dt is None:
        return '-'

    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt)
        except:
            return dt

    if isinstance(dt, datetime):
        return dt.strftime('%Y-%m-%d %H:%M')

    return str(dt)


def invoice_type_label(invoice_type):
    """تسمية نوع الفاتورة"""
    types = {
        'cash': 'نقدي',
        'installment': 'تقسيط'
    }
    return types.get(invoice_type, invoice_type)


def invoice_status_label(status):
    """تسمية حالة الفاتورة"""
    statuses = {
        'active': 'نشطة',
        'completed': 'مكتملة',
        'cancelled': 'ملغاة'
    }
    return statuses.get(status, status)


def installment_status_label(status):
    """تسمية حالة القسط"""
    statuses = {
        'pending': 'معلق',
        'partial': 'جزئي',
        'paid': 'مدفوع',
        'overdue': 'متأخر'
    }
    return statuses.get(status, status)


def user_role_label(role):
    """تسمية دور المستخدم"""
    roles = {
        'admin': 'مدير',
        'cashier': 'كاشير',
        'sales': 'موظف مبيعات'
    }
    return roles.get(role, role)


def payment_method_label(method):
    """تسمية طريقة الدفع"""
    methods = {
        'cash': 'نقدي',
        'card': 'بطاقة',
        'transfer': 'تحويل'
    }
    return methods.get(method, method)


def get_pagination_info(page, per_page, total):
    """حساب معلومات الصفحات"""
    total_pages = (total + per_page - 1) // per_page

    return {
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': total_pages,
        'has_prev': page > 1,
        'has_next': page < total_pages,
        'start_item': (page - 1) * per_page + 1 if total > 0 else 0,
        'end_item': min(page * per_page, total),
    }
