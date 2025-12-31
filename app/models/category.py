"""
نموذج التصنيف
"""
from datetime import datetime
from app import db


class Category(db.Model):
    """نموذج التصنيف"""
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    parent_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    icon = db.Column(db.String(50))
    color = db.Column(db.String(20), default='#1e88e5')
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # العلاقات
    products = db.relationship('Product', backref='category', lazy='dynamic')
    children = db.relationship('Category', backref=db.backref(
        'parent', remote_side=[id]), lazy='dynamic')

    @property
    def products_count(self):
        """عدد المنتجات في التصنيف"""
        return self.products.count()

    @classmethod
    def get_all_with_count(cls):
        """جلب التصنيفات مع عدد المنتجات"""
        return cls.query.order_by(cls.sort_order, cls.name).all()

    def to_dict(self):
        """تحويل لـ Dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'parent_id': self.parent_id,
            'icon': self.icon,
            'color': self.color,
            'sort_order': self.sort_order,
            'is_active': self.is_active,
            'products_count': self.products_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f'<Category {self.name}>'
