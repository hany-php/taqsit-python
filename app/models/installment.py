"""
نموذج القسط
"""
from datetime import datetime, date
from app import db


class Installment(db.Model):
    """نموذج القسط"""
    __tablename__ = 'installments'

    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey(
        'invoices.id', ondelete='CASCADE'), nullable=False)
    installment_number = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    paid_amount = db.Column(db.Numeric(10, 2), default=0)
    remaining_amount = db.Column(db.Numeric(10, 2))
    due_date = db.Column(db.Date, nullable=False)
    paid_date = db.Column(db.Date)
    # pending, partial, paid, overdue
    status = db.Column(db.String(20), default='pending')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # العلاقات
    payments = db.relationship(
        'Payment', backref='installment', lazy='dynamic')

    @property
    def days_overdue(self):
        """أيام التأخير"""
        if self.status in ['pending', 'partial', 'overdue'] and self.due_date < date.today():
            return (date.today() - self.due_date).days
        return 0

    @property
    def is_overdue(self):
        """هل القسط متأخر؟"""
        return self.days_overdue > 0

    @classmethod
    def get_today(cls):
        """جلب أقساط اليوم"""
        today = date.today()
        return cls.query.join(cls.invoice).filter(
            cls.due_date == today,
            cls.status.in_(['pending', 'partial'])
        ).all()

    @classmethod
    def get_overdue(cls):
        """جلب الأقساط المتأخرة"""
        today = date.today()
        return cls.query.join(cls.invoice).filter(
            cls.due_date < today,
            cls.status.in_(['pending', 'partial', 'overdue'])
        ).order_by(cls.due_date).all()

    @classmethod
    def update_overdue_status(cls):
        """تحديث حالة الأقساط المتأخرة"""
        today = date.today()
        cls.query.filter(
            cls.due_date < today,
            cls.status.in_(['pending', 'partial'])
        ).update({'status': 'overdue'}, synchronize_session=False)
        db.session.commit()

    @classmethod
    def get_stats(cls):
        """إحصائيات الأقساط"""
        today = date.today()

        # الأقساط المتأخرة
        overdue = cls.query.filter(
            cls.due_date < today,
            cls.status.in_(['pending', 'partial', 'overdue'])
        ).all()

        overdue_count = len(overdue)
        overdue_amount = sum(float(i.remaining_amount or i.amount)
                             for i in overdue)

        # أقساط اليوم
        today_installments = cls.query.filter(
            cls.due_date == today,
            cls.status.in_(['pending', 'partial'])
        ).all()

        today_count = len(today_installments)
        today_amount = sum(float(i.remaining_amount or i.amount)
                           for i in today_installments)

        return {
            'overdue_count': overdue_count,
            'overdue_amount': overdue_amount,
            'today_count': today_count,
            'today_amount': today_amount,
        }

    def pay(self, amount, user_id=None, notes=None):
        """دفع جزء أو كل القسط"""
        from app.models.payment import Payment

        # إنشاء رقم إيصال
        receipt_number = f"RCP-{datetime.utcnow().strftime('%Y%m%d')}-{Installment.query.count():04d}"

        # إنشاء الدفعة
        payment = Payment(
            invoice_id=self.invoice_id,
            installment_id=self.id,
            amount=amount,
            payment_method='cash',
            receipt_number=receipt_number,
            user_id=user_id,
            notes=notes
        )
        db.session.add(payment)

        # تحديث القسط
        self.paid_amount = float(self.paid_amount or 0) + amount
        self.remaining_amount = float(self.amount) - float(self.paid_amount)

        if self.remaining_amount <= 0:
            self.status = 'paid'
            self.paid_date = date.today()
            self.remaining_amount = 0
        else:
            self.status = 'partial'

        # تحديث الفاتورة
        self.invoice.update_amounts()

        db.session.commit()

        return payment

    def to_dict(self):
        """تحويل لـ Dictionary"""
        return {
            'id': self.id,
            'invoice_id': self.invoice_id,
            'invoice_number': self.invoice.invoice_number if self.invoice else None,
            'customer_name': self.invoice.customer.full_name if self.invoice and self.invoice.customer else None,
            'customer_phone': self.invoice.customer.phone if self.invoice and self.invoice.customer else None,
            'installment_number': self.installment_number,
            'amount': float(self.amount) if self.amount else 0,
            'paid_amount': float(self.paid_amount) if self.paid_amount else 0,
            'remaining_amount': float(self.remaining_amount) if self.remaining_amount else 0,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'paid_date': self.paid_date.isoformat() if self.paid_date else None,
            'status': self.status,
            'days_overdue': self.days_overdue,
            'notes': self.notes,
        }

    def __repr__(self):
        return f'<Installment {self.installment_number} of Invoice {self.invoice_id}>'
