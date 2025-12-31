"""
نموذج خطط التقسيط
"""
from datetime import datetime
from app import db


class InstallmentPlan(db.Model):
    """نموذج خطة التقسيط"""
    __tablename__ = 'installment_plans'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    months = db.Column(db.Integer, nullable=False)
    interest_rate = db.Column(db.Numeric(5, 2), default=0)  # نسبة الزيادة %
    min_down_payment = db.Column(db.Numeric(
        5, 2), default=0)  # الحد الأدنى للمقدم %
    is_active = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @classmethod
    def get_active_plans(cls):
        """جلب الخطط النشطة"""
        return cls.query.filter_by(is_active=True).order_by(cls.sort_order, cls.months).all()

    @classmethod
    def get_all_plans(cls):
        """جلب جميع الخطط"""
        return cls.query.order_by(cls.sort_order, cls.months).all()

    def to_dict(self):
        """تحويل لـ Dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'months': self.months,
            'interest_rate': float(self.interest_rate) if self.interest_rate else 0,
            'min_down_payment': float(self.min_down_payment) if self.min_down_payment else 0,
            'is_active': self.is_active,
            'sort_order': self.sort_order
        }

    def __repr__(self):
        return f'<InstallmentPlan {self.name}>'
