"""
نموذج المدفوعات
"""
from datetime import datetime, date
from app import db


class Payment(db.Model):
    """نموذج المدفوعة"""
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey(
        'invoices.id'), nullable=False)
    installment_id = db.Column(db.Integer, db.ForeignKey('installments.id'))
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_method = db.Column(
        db.String(20), default='cash')  # cash, card, transfer
    receipt_number = db.Column(db.String(50), index=True)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @classmethod
    def get_today(cls):
        """جلب مدفوعات اليوم"""
        today = date.today()
        return cls.query.filter(
            db.func.date(cls.payment_date) == today
        ).order_by(cls.payment_date.desc()).all()

    @classmethod
    def get_today_total(cls):
        """إجمالي مدفوعات اليوم"""
        today = date.today()
        result = db.session.query(
            db.func.coalesce(db.func.sum(cls.amount), 0)
        ).filter(
            db.func.date(cls.payment_date) == today
        ).scalar()
        return float(result) if result else 0

    @classmethod
    def get_by_date_range(cls, from_date, to_date):
        """جلب مدفوعات فترة معينة"""
        return cls.query.filter(
            db.func.date(cls.payment_date) >= from_date,
            db.func.date(cls.payment_date) <= to_date
        ).order_by(cls.payment_date.desc()).all()

    @classmethod
    def get_total_by_date_range(cls, from_date, to_date):
        """إجمالي مدفوعات فترة"""
        result = db.session.query(
            db.func.coalesce(db.func.sum(cls.amount), 0)
        ).filter(
            db.func.date(cls.payment_date) >= from_date,
            db.func.date(cls.payment_date) <= to_date
        ).scalar()
        return float(result) if result else 0

    def get_method_label(self):
        """الحصول على اسم طريقة الدفع"""
        methods = {
            'cash': 'نقدي',
            'card': 'بطاقة',
            'transfer': 'تحويل'
        }
        return methods.get(self.payment_method, self.payment_method)

    def to_dict(self):
        """تحويل لـ Dictionary"""
        return {
            'id': self.id,
            'invoice_id': self.invoice_id,
            'invoice_number': self.invoice.invoice_number if self.invoice else None,
            'customer_name': self.invoice.customer.full_name if self.invoice and self.invoice.customer else None,
            'installment_id': self.installment_id,
            'amount': float(self.amount) if self.amount else 0,
            'payment_method': self.payment_method,
            'payment_method_label': self.get_method_label(),
            'receipt_number': self.receipt_number,
            'payment_date': self.payment_date.isoformat() if self.payment_date else None,
            'user_id': self.user_id,
            'user_name': self.user.full_name if self.user else None,
            'notes': self.notes,
        }

    def __repr__(self):
        return f'<Payment {self.receipt_number}>'
