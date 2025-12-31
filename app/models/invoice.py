"""
نموذج الفاتورة وبنود الفاتورة
"""
from datetime import datetime
from app import db


class Invoice(db.Model):
    """نموذج الفاتورة"""
    __tablename__ = 'invoices'

    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(
        db.String(50), unique=True, nullable=False, index=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    invoice_type = db.Column(
        db.String(20), nullable=False)  # cash, installment
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    down_payment = db.Column(db.Numeric(10, 2), default=0)
    paid_amount = db.Column(db.Numeric(10, 2), default=0)
    remaining_amount = db.Column(db.Numeric(10, 2), default=0)
    monthly_installment = db.Column(db.Numeric(10, 2))
    installment_months = db.Column(db.Integer)
    # active, completed, cancelled
    status = db.Column(db.String(20), default='active')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # العلاقات
    items = db.relationship('InvoiceItem', backref='invoice',
                            lazy='dynamic', cascade='all, delete-orphan')
    installments = db.relationship(
        'Installment', backref='invoice', lazy='dynamic', cascade='all, delete-orphan')
    payments = db.relationship('Payment', backref='invoice', lazy='dynamic')

    @staticmethod
    def generate_invoice_number():
        """إنشاء رقم فاتورة جديد"""
        today = datetime.utcnow().strftime('%Y%m%d')
        last_invoice = Invoice.query.filter(
            Invoice.invoice_number.like(f'INV-{today}%')
        ).order_by(Invoice.id.desc()).first()

        if last_invoice:
            last_num = int(last_invoice.invoice_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1

        return f'INV-{today}-{new_num:04d}'

    @property
    def paid_installments_count(self):
        """عدد الأقساط المدفوعة"""
        return self.installments.filter_by(status='paid').count()

    @property
    def pending_installments_count(self):
        """عدد الأقساط المعلقة"""
        from app.models.installment import Installment
        return self.installments.filter(
            Installment.status.in_(['pending', 'partial', 'overdue'])
        ).count()

    def update_amounts(self):
        """تحديث المبالغ"""
        total_paid = sum(float(p.amount) for p in self.payments)
        self.paid_amount = total_paid
        self.remaining_amount = float(self.total_amount) - total_paid

        if self.remaining_amount <= 0:
            self.status = 'completed'
            self.remaining_amount = 0

        db.session.commit()

    def to_dict(self, include_items=False, include_installments=False):
        """تحويل لـ Dictionary"""
        data = {
            'id': self.id,
            'invoice_number': self.invoice_number,
            'customer_id': self.customer_id,
            'customer_name': self.customer.full_name if self.customer else None,
            'customer_phone': self.customer.phone if self.customer else None,
            'user_id': self.user_id,
            'user_name': self.user.full_name if self.user else None,
            'invoice_type': self.invoice_type,
            'total_amount': float(self.total_amount) if self.total_amount else 0,
            'down_payment': float(self.down_payment) if self.down_payment else 0,
            'paid_amount': float(self.paid_amount) if self.paid_amount else 0,
            'remaining_amount': float(self.remaining_amount) if self.remaining_amount else 0,
            'monthly_installment': float(self.monthly_installment) if self.monthly_installment else 0,
            'installment_months': self.installment_months,
            'status': self.status,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

        if include_items:
            data['items'] = [item.to_dict() for item in self.items]

        if include_installments:
            data['installments'] = [inst.to_dict()
                                    for inst in self.installments]

        return data

    def __repr__(self):
        return f'<Invoice {self.invoice_number}>'


class InvoiceItem(db.Model):
    """نموذج بند الفاتورة"""
    __tablename__ = 'invoice_items'

    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey(
        'invoices.id', ondelete='CASCADE'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    product_name = db.Column(db.String(200))
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    total_price = db.Column(db.Numeric(10, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """تحويل لـ Dictionary"""
        return {
            'id': self.id,
            'invoice_id': self.invoice_id,
            'product_id': self.product_id,
            'product_name': self.product_name,
            'quantity': self.quantity,
            'unit_price': float(self.unit_price) if self.unit_price else 0,
            'total_price': float(self.total_price) if self.total_price else 0,
        }

    def __repr__(self):
        return f'<InvoiceItem {self.product_name}>'
