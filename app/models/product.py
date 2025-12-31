"""
نموذج المنتج
"""
from datetime import datetime
from app import db


class Product(db.Model):
    """نموذج المنتج"""
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    barcode = db.Column(db.String(50), index=True)
    sku = db.Column(db.String(50))
    cash_price = db.Column(db.Numeric(10, 2), nullable=False)
    installment_price = db.Column(db.Numeric(10, 2))
    cost_price = db.Column(db.Numeric(10, 2))
    quantity = db.Column(db.Integer, default=0)
    min_quantity = db.Column(db.Integer, default=5)
    image = db.Column(db.String(255))
    brand = db.Column(db.String(100))
    model = db.Column(db.String(100))
    warranty_months = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # العلاقات
    invoice_items = db.relationship(
        'InvoiceItem', backref='product', lazy='dynamic')

    @property
    def is_low_stock(self):
        """هل المخزون منخفض؟"""
        return self.quantity <= self.min_quantity

    @property
    def profit_margin(self):
        """هامش الربح"""
        if self.cost_price and self.cash_price:
            return float(self.cash_price) - float(self.cost_price)
        return 0

    @classmethod
    def get_active(cls):
        """جلب المنتجات النشطة"""
        return cls.query.filter_by(is_active=True).order_by(cls.name).all()

    @classmethod
    def get_low_stock(cls):
        """جلب المنتجات منخفضة المخزون"""
        return cls.query.filter(
            cls.quantity <= cls.min_quantity,
            cls.is_active == True
        ).all()

    @classmethod
    def search(cls, query, limit=20):
        """بحث في المنتجات"""
        search = f'%{query}%'
        return cls.query.filter(
            cls.is_active == True,
            db.or_(
                cls.name.ilike(search),
                cls.barcode.ilike(search),
                cls.brand.ilike(search)
            )
        ).limit(limit).all()

    def update_quantity(self, change):
        """تحديث الكمية"""
        self.quantity += change
        db.session.commit()

    def to_dict(self):
        """تحويل لـ Dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else None,
            'barcode': self.barcode,
            'sku': self.sku,
            'cash_price': float(self.cash_price) if self.cash_price else 0,
            'installment_price': float(self.installment_price) if self.installment_price else 0,
            'cost_price': float(self.cost_price) if self.cost_price else 0,
            'quantity': self.quantity,
            'min_quantity': self.min_quantity,
            'image': self.image,
            'brand': self.brand,
            'model': self.model,
            'warranty_months': self.warranty_months,
            'is_active': self.is_active,
            'is_low_stock': self.is_low_stock,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f'<Product {self.name}>'
