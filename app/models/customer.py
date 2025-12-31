"""
نموذج العميل
"""
from datetime import datetime
from app import db


class Customer(db.Model):
    """نموذج العميل"""
    __tablename__ = 'customers'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False, index=True)
    phone2 = db.Column(db.String(20))
    national_id = db.Column(db.String(20), index=True)
    national_id_image = db.Column(db.String(255))
    address = db.Column(db.Text)
    city = db.Column(db.String(50))
    work_address = db.Column(db.Text)
    work_phone = db.Column(db.String(20))
    guarantor_name = db.Column(db.String(100))
    guarantor_phone = db.Column(db.String(20))
    guarantor_national_id = db.Column(db.String(20))
    credit_limit = db.Column(db.Numeric(10, 2), default=0)
    notes = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # العلاقات
    invoices = db.relationship('Invoice', backref='customer', lazy='dynamic')

    @property
    def balance(self):
        """الرصيد المستحق"""
        from app.models.invoice import Invoice
        result = db.session.query(
            db.func.coalesce(db.func.sum(Invoice.remaining_amount), 0)
        ).filter(
            Invoice.customer_id == self.id,
            Invoice.status == 'active'
        ).scalar()
        return float(result) if result else 0

    @property
    def active_invoices_count(self):
        """عدد الفواتير النشطة"""
        return self.invoices.filter_by(status='active').count()

    @classmethod
    def search(cls, query, limit=20):
        """بحث في العملاء"""
        search = f'%{query}%'
        return cls.query.filter(
            db.or_(
                cls.full_name.ilike(search),
                cls.phone.ilike(search),
                cls.national_id.ilike(search)
            )
        ).limit(limit).all()

    def get_invoices(self):
        """جلب فواتير العميل"""
        return self.invoices.order_by(db.desc('created_at')).all()

    def get_payments(self):
        """جلب مدفوعات العميل"""
        from app.models.payment import Payment
        from app.models.invoice import Invoice
        return Payment.query.join(Invoice).filter(
            Invoice.customer_id == self.id
        ).order_by(db.desc(Payment.payment_date)).all()

    def to_dict(self):
        """تحويل لـ Dictionary"""
        return {
            'id': self.id,
            'full_name': self.full_name,
            'phone': self.phone,
            'phone2': self.phone2,
            'national_id': self.national_id,
            'address': self.address,
            'city': self.city,
            'work_address': self.work_address,
            'work_phone': self.work_phone,
            'guarantor_name': self.guarantor_name,
            'guarantor_phone': self.guarantor_phone,
            'guarantor_national_id': self.guarantor_national_id,
            'credit_limit': float(self.credit_limit) if self.credit_limit else 0,
            'notes': self.notes,
            'is_active': self.is_active,
            'balance': self.balance,
            'active_invoices_count': self.active_invoices_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f'<Customer {self.full_name}>'
